#!/usr/bin/env python3
"""Mirror a local paper reading packet to a Feishu/Lark Docx document."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from organize_paper import (
    CORE_FIELDS,
    build_one_sentence_summary,
    extract_core_content,
    extract_one_sentence_summary,
)


def load_metadata(path: str | None, folder: str | None) -> tuple[dict[str, Any], Path]:
    if path:
        metadata_path = Path(path).expanduser().resolve()
    elif folder:
        metadata_path = Path(folder).expanduser().resolve() / "metadata.json"
    else:
        raise SystemExit("Pass --metadata or --paper-folder.")
    if not metadata_path.exists():
        raise SystemExit(f"metadata.json not found: {metadata_path}")
    return json.loads(metadata_path.read_text(encoding="utf-8")), metadata_path


def read_text(path: str | Path) -> str:
    candidate = Path(path).expanduser()
    return candidate.read_text(encoding="utf-8") if candidate.exists() else ""


def parse_json_output(stdout: str) -> dict[str, Any]:
    start = stdout.find("{")
    if start == -1:
        raise SystemExit(f"Expected JSON from lark-cli, got: {stdout[:500]}")
    return json.loads(stdout[start:])


def run_lark(args: list[str], content: str | None = None) -> dict[str, Any]:
    tmp_path: Path | None = None
    command = ["lark-cli", *args]
    if content is not None:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".md", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        command.extend(["--content", f"@{tmp_path}"])
    try:
        proc = subprocess.run(command, text=True, capture_output=True, check=False)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise SystemExit(f"lark-cli failed ({proc.returncode}): {' '.join(command)}\n{detail}")
    return parse_json_output(proc.stdout)


def clean_highlighted(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value or "").strip()


def safe_search_query(title: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff\s-]+", " ", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    parts = cleaned.split()
    if len(parts) > 4:
        cleaned = " ".join(parts[:4])
    return cleaned or title


def search_documents(title: str, page_size: int = 10) -> list[dict[str, Any]]:
    response = run_lark(
        [
            "drive",
            "+search",
            "--query",
            safe_search_query(title),
            "--doc-types",
            "docx,wiki",
            "--page-size",
            str(page_size),
            "--json",
        ]
    )
    data = response.get("data") or {}
    return list(data.get("results") or [])


def candidate_info(result: dict[str, Any]) -> dict[str, str]:
    meta = result.get("result_meta") or {}
    return {
        "entity_type": str(result.get("entity_type") or ""),
        "title": clean_highlighted(str(result.get("title_highlighted") or "")),
        "token": str(meta.get("token") or ""),
        "url": str(meta.get("url") or ""),
        "doc_types": str(meta.get("doc_types") or ""),
    }


def exact_title_match(results: list[dict[str, Any]], title: str) -> dict[str, str] | None:
    matches = [candidate_info(result) for result in results]
    exact = [item for item in matches if item["title"].strip().lower() == title.strip().lower()]
    return exact[0] if len(exact) == 1 else None


def find_key(value: Any, names: set[str]) -> str:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in names and isinstance(item, str) and item:
                return item
        for item in value.values():
            found = find_key(item, names)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = find_key(item, names)
            if found:
                return found
    return ""


def markdown_escape(value: object) -> str:
    text = str(value or "").replace("\n", "<br>")
    return text.replace("|", "\\|")


def metadata_table(metadata: dict[str, Any], metadata_path: Path) -> str:
    rows = [
        ("Title", metadata.get("title")),
        ("Authors", metadata.get("authors")),
        ("Publication", metadata.get("publication") or metadata.get("venue")),
        ("Date", metadata.get("date") or metadata.get("year")),
        ("Paper link", metadata.get("paper_url") or metadata.get("url")),
        ("Web/project link", metadata.get("web_url")),
        ("GitHub link", metadata.get("github_url")),
        ("Zotero item key", metadata.get("zotero_key")),
        ("BibTeX key", metadata.get("bibtex_key")),
        ("Local folder", metadata.get("local_folder") or str(metadata_path.parent)),
        ("Note path", metadata.get("note_path")),
    ]
    body = ["| Field | Value |", "|---|---|"]
    for key, value in rows:
        body.append(f"| {markdown_escape(key)} | {markdown_escape(value)} |")
    return "\n".join(body)


def tag_block(metadata: dict[str, Any]) -> str:
    rows = [
        ("Domain tags", metadata.get("domain_tags") or []),
        ("Method tags", metadata.get("method_tags") or []),
        ("Project tags", metadata.get("project_tags") or []),
        ("Zotero tags", metadata.get("zotero_tags") or []),
    ]
    lines = []
    for label, values in rows:
        if isinstance(values, str):
            values = [values]
        joined = ", ".join(str(value) for value in values if value)
        lines.append(f"- **{label}**: {joined}")
    return "\n".join(lines)


def build_content(metadata: dict[str, Any], metadata_path: Path) -> str:
    note_path = metadata.get("note_path") or str(metadata_path.parent / "note.md")
    note = read_text(str(note_path))
    core = extract_core_content(note)
    for field in CORE_FIELDS:
        if not metadata.get(field) and core.get(field):
            metadata[field] = core[field]

    one_sentence = str(metadata.get("one_sentence_summary") or "").strip()
    if not one_sentence:
        one_sentence = extract_one_sentence_summary(note)
    if not one_sentence:
        metadata["one_sentence_summary"] = ""
        one_sentence = build_one_sentence_summary(metadata)
    metadata["one_sentence_summary"] = one_sentence
    title = str(metadata.get("title") or metadata.get("short_title") or "Untitled Paper")
    content = [
        f"# {title}",
        "",
        f"> {one_sentence}" if one_sentence else "> 一句话概览：暂无。",
        "",
        "## Metadata",
        "",
        metadata_table(metadata, metadata_path),
        "",
        "## Core Content",
        "",
        f"- **Topic**: {metadata.get('topic') or ''}",
        f"- **Problem**: {metadata.get('problem') or ''}",
        f"- **Method**: {metadata.get('method') or ''}",
        f"- **Innovation**: {metadata.get('innovation') or ''}",
        f"- **Significance**: {metadata.get('significance') or ''}",
        f"- **One-sentence summary**: {one_sentence}",
        "",
        "## Tags",
        "",
        tag_block(metadata),
        "",
        "## Full Reading Note",
        "",
        note.strip(),
        "",
    ]
    return "\n".join(content)


def write_metadata(metadata_path: Path, metadata: dict[str, Any]) -> None:
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", help="Path to metadata.json")
    parser.add_argument("--paper-folder", help="Paper folder containing metadata.json")
    parser.add_argument("--doc", help="Explicit Feishu/Lark doc URL or token to update")
    parser.add_argument("--parent-token", help="Parent folder or wiki-node token for new docs")
    parser.add_argument("--parent-position", default="", help="Parent position for docs +create, e.g. my_library")
    parser.add_argument("--force-create", action="store_true", help="Create a new doc even if a candidate exists")
    parser.add_argument("--no-search", action="store_true", help="Skip title search when no doc token is known")
    parser.add_argument("--page-size", type=int, default=10)
    parser.add_argument("--emit-content", help="Write the rendered Markdown content to this local path")
    parser.add_argument("--yes", action="store_true", help="Create/update Feishu and write feishu_doc_token back")
    args = parser.parse_args()

    metadata, metadata_path = load_metadata(args.metadata, args.paper_folder)
    title = str(metadata.get("title") or metadata.get("short_title") or "").strip()
    if not title:
        raise SystemExit("metadata.json must contain title or short_title.")

    content = build_content(metadata, metadata_path)
    if args.emit_content:
        Path(args.emit_content).expanduser().resolve().write_text(content, encoding="utf-8")

    candidates: list[dict[str, Any]] = []
    matched = None
    known_doc = args.doc or str(metadata.get("feishu_doc_url") or metadata.get("feishu_doc_token") or "").strip()
    if not known_doc and not args.no_search and not args.force_create:
        candidates = search_documents(title, page_size=args.page_size)
        matched = exact_title_match(candidates, title)
        if matched:
            known_doc = matched.get("url") or matched.get("token") or ""

    action = "create" if args.force_create or not known_doc else "update"
    plan = {
        "metadata": str(metadata_path),
        "title": title,
        "action": action,
        "known_doc": known_doc,
        "matched_candidate": matched,
        "candidate_count": len(candidates),
        "write": bool(args.yes),
    }
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    if not args.yes:
        return 0

    if action == "update":
        response = run_lark(
            [
                "docs",
                "+update",
                "--api-version",
                "v2",
                "--doc",
                known_doc,
                "--command",
                "overwrite",
                "--doc-format",
                "markdown",
                "--json",
            ],
            content=content,
        )
    else:
        command = [
            "docs",
            "+create",
            "--api-version",
            "v2",
            "--doc-format",
            "markdown",
            "--json",
        ]
        if args.parent_token:
            command.extend(["--parent-token", args.parent_token])
        if args.parent_position:
            command.extend(["--parent-position", args.parent_position])
        response = run_lark(command, content=content)

    token = find_key(response, {"document_id", "document_token", "doc_token", "token"}) or known_doc
    url = find_key(response, {"url"}) or (matched or {}).get("url", "")
    metadata["feishu_doc_token"] = token
    if url:
        metadata["feishu_doc_url"] = url
    metadata["feishu_synced_at"] = datetime.now().isoformat(timespec="seconds")
    write_metadata(metadata_path, metadata)
    print(json.dumps({"synced": True, "token": token, "url": url}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
