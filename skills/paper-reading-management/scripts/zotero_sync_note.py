#!/usr/bin/env python3
"""Sync a paper reading packet's one-sentence summary to Zotero Style remark."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

from zotero_api import load_item, write_metadata, write_tags


CORE_FIELDS = ("topic", "problem", "method", "innovation", "significance")
KIND_TAGS = {"#会议论文", "#期刊论文", "#预印本", "#网页资料"}


def load_metadata(path: str | None, folder: str | None) -> tuple[dict, Path | None]:
    if path:
        metadata_path = Path(path).expanduser().resolve()
    elif folder:
        metadata_path = Path(folder).expanduser().resolve() / "metadata.json"
    else:
        return {}, None
    if not metadata_path.exists():
        raise SystemExit(f"metadata.json not found: {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8")), metadata_path


def read_note(metadata: dict, metadata_path: Path | None) -> str:
    note = metadata.get("note_path") or ""
    if not note and metadata_path is not None:
        note = str(metadata_path.parent / "note.md")
    if not note:
        return ""
    note_path = Path(str(note)).expanduser()
    if not note_path.exists():
        return ""
    return note_path.read_text(encoding="utf-8")


def extract_core_from_note(note: str) -> dict[str, str]:
    core: dict[str, str] = {}
    pattern = re.compile(
        r"^\s*(?:[-*]\s*)?\*\*(Topic|Problem|Method|Innovation|Significance)\*\*"
        r"\s*(?:—|--|:|：)\s*(.+?)\s*$"
    )
    for line in note.splitlines():
        match = pattern.match(line)
        if match:
            core.setdefault(match.group(1).lower(), match.group(2).strip())
    return core


def extract_one_sentence(note: str) -> str:
    patterns = [
        r"^\s*(?:[-*]\s*)?\*\*(?:一句话总结|One-sentence summary)\*\*\s*(?:[:：])\s*(.+?)\s*$",
        r"^\s*(?:[-*]\s*)?(?:一句话总结|One-sentence summary)\s*(?:[:：])\s*(.+?)\s*$",
    ]
    for pattern in patterns:
        for line in note.splitlines():
            match = re.match(pattern, line, flags=re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return ""


def normalize_clause(text: object) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    return cleaned.rstrip("；;，,。.")


def method_phrase(text: object) -> str:
    cleaned = normalize_clause(text)
    cleaned = re.sub(r"^(?:本文|论文)?\s*提出", "提出", cleaned)
    if cleaned.startswith(("提出", "采用", "使用", "通过", "构建", "设计")):
        return cleaned
    return f"采用{cleaned}" if cleaned else ""


def build_one_sentence(metadata: dict, note: str) -> str:
    explicit = str(metadata.get("one_sentence_summary") or "").strip()
    if explicit:
        return explicit
    from_note = extract_one_sentence(note)
    if from_note:
        return from_note

    core = {field: normalize_clause(metadata.get(field)) for field in CORE_FIELDS}
    note_core = extract_core_from_note(note)
    for field in CORE_FIELDS:
        if not core[field] and note_core.get(field):
            core[field] = normalize_clause(note_core[field])
    available = [core[field] for field in CORE_FIELDS if core[field]]
    if len(available) >= 3:
        title = normalize_clause(metadata.get("title")) or "该论文"
        topic = core["topic"] or "目标人工智能问题"
        method = core["method"] or "一种专门方法"
        return f"{title}聚焦{topic}，并通过{method}解决相关研究问题。"
    return ""


def tag_names(tags: list[dict]) -> list[str]:
    names: list[str] = []
    for tag in tags:
        name = tag.get("tag")
        if name and name not in names:
            names.append(name)
    return names


def desired_zotero_tags(metadata: dict) -> list[str]:
    tags: list[str] = []
    value = metadata.get("zotero_tags") or []
    if isinstance(value, str):
        value = [value]
    for tag in value:
        if tag and tag not in tags:
            tags.append(str(tag))
    if len(tags) != 2:
        raise SystemExit("metadata.zotero_tags must contain exactly two unique tags.")
    kind_tags = [tag for tag in tags if tag in KIND_TAGS]
    source_tags = [tag for tag in tags if tag not in KIND_TAGS and tag.startswith("#")]
    if len(kind_tags) != 1 or len(source_tags) != 1:
        raise SystemExit(
            "metadata.zotero_tags must contain one kind tag and one #venue/source/version tag."
        )
    return [kind_tags[0], source_tags[0]]


def upsert_remark(extra: object, summary: str) -> str:
    """Store Zotero Style's 简记 as a `remark:` line in Zotero Extra."""
    kept = [
        line
        for line in str(extra or "").splitlines()
        if not re.match(r"^\s*remark\s*:", line, flags=re.IGNORECASE)
    ]
    lines = [f"remark: {summary}", *kept]
    return "\n".join(line for line in lines if line.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", help="Path to metadata.json")
    parser.add_argument("--paper-folder", help="Paper folder containing metadata.json")
    parser.add_argument("--item-key", help="Override Zotero item key")
    parser.add_argument("--summary", help="Override one-sentence summary")
    parser.add_argument(
        "--sync-tags",
        action="store_true",
        help="Replace all item tags with exactly the two metadata.zotero_tags",
    )
    parser.add_argument("--yes", action="store_true", help="Write to Zotero")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    metadata, metadata_path = load_metadata(args.metadata, args.paper_folder)
    note = read_note(metadata, metadata_path)
    item_key = args.item_key or str(metadata.get("zotero_key") or "").strip()
    if not item_key:
        raise SystemExit("Missing Zotero item key. Pass --item-key or set zotero_key in metadata.json.")

    item = load_item(item_key)
    data = item.get("data") or {}
    if data.get("itemType") == "attachment":
        raise SystemExit(
            f"{item_key} is a Zotero attachment. Use the parent top-level item key instead."
        )

    summary = (args.summary or "").strip() or build_one_sentence(metadata, note)
    if not summary:
        raise SystemExit("Could not determine one-sentence summary from metadata or note.md.")

    current_tags = tag_names(data.get("tags") or [])
    target_tags = desired_zotero_tags(metadata) if args.sync_tags else list(current_tags)

    extra_before = data.get("extra") or ""
    extra_after = upsert_remark(extra_before, summary)

    plan = {
        "item_key": item_key,
        "title": data.get("title"),
        "extra_before": extra_before,
        "extra_after": extra_after,
        "remark_after": summary,
        "tags_before": current_tags,
        "tags_after": target_tags,
        "changed": extra_before != extra_after or target_tags != current_tags,
        "write": bool(args.yes),
    }

    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if not args.yes:
        return 0
    if not plan["changed"]:
        return 0

    write_metadata(item_key, {"extra": extra_after})
    if args.sync_tags and target_tags != current_tags:
        write_tags(item_key, target_tags)
    if metadata_path is not None:
        metadata["zotero_remark_synced_at"] = datetime.now().isoformat(timespec="seconds")
        if args.sync_tags:
            metadata["zotero_tags_synced_at"] = metadata["zotero_remark_synced_at"]
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
