#!/usr/bin/env python3
"""Build the root-level paper directory tree from metadata.json files."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def load_records(root: Path) -> list[dict]:
    records: list[dict] = []
    for metadata_path in sorted(root.glob("**/metadata.json")):
        if "_index" in metadata_path.parts:
            continue
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        folder = metadata_path.parent
        metadata.setdefault("local_folder", str(folder))
        metadata.setdefault("note_path", str(folder / "note.md"))
        retrieval_path = folder / "retrieval.md"
        metadata.setdefault("retrieval_path", str(retrieval_path) if retrieval_path.exists() else "")
        metadata["_folder_rel"] = folder.relative_to(root).as_posix()
        metadata["_note_rel"] = Path(metadata["note_path"]).relative_to(root).as_posix() if Path(metadata["note_path"]).is_absolute() and Path(metadata["note_path"]).exists() else (folder / "note.md").relative_to(root).as_posix()
        metadata["_retrieval_rel"] = Path(metadata["retrieval_path"]).relative_to(root).as_posix() if metadata.get("retrieval_path") and Path(metadata["retrieval_path"]).is_absolute() and Path(metadata["retrieval_path"]).exists() else ""
        records.append(metadata)
    return sorted(records, key=lambda item: (str(item.get("date") or item.get("year") or ""), str(item.get("title") or "").lower()), reverse=True)


def md_link(label: str, rel_path: str) -> str:
    return f"[{label}]({rel_path})" if rel_path else ""


def build_index_md(root: Path, records: list[dict]) -> str:
    by_collection: dict[str, list[dict]] = {}
    for record in records:
        collection = record.get("collection_path") or str(Path(record.get("_folder_rel", "")).parent)
        by_collection.setdefault(str(collection), []).append(record)

    lines = ["# Paper Directory", "", f"Root: `{root}`", ""]
    for collection in sorted(by_collection, key=str.lower):
        lines.extend([f"## {collection}", ""])
        for record in sorted(by_collection[collection], key=lambda item: str(item.get("title") or "").lower()):
            short = record.get("short_title") or record.get("title") or "Untitled"
            publication = record.get("publication") or record.get("venue") or ""
            date = record.get("date") or record.get("year") or ""
            lines.extend(
                [
                    f"- {md_link(str(short), str(record.get('_note_rel') or ''))} ({publication or date})",
                ]
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_retrieval_text(records: list[dict]) -> str:
    lines = []
    for record in records:
        title = record.get("title") or "Untitled"
        paper_url = record.get("paper_url") or record.get("url") or ""
        lines.extend(
            [
                f"# {record.get('short_title') or title}",
                "",
                f"- Title: {title}",
                f"- Paper link: {paper_url}",
                f"- Web/project link: {record.get('web_url') or ''}",
                f"- GitHub link: {record.get('github_url') or ''}",
                "",
                "## Core Content",
                "",
                f"- **Topic**: {record.get('topic') or ''}",
                f"- **Problem**: {record.get('problem') or ''}",
                f"- **Method**: {record.get('method') or ''}",
                f"- **Innovation**: {record.get('innovation') or ''}",
                f"- **Significance**: {record.get('significance') or ''}",
                "",
                "## Bibliographic Metadata",
                "",
                f"- Authors: {record.get('authors') or ''}",
                f"- Publication: {record.get('publication') or record.get('venue') or ''}",
                f"- Date: {record.get('date') or record.get('year') or ''}",
                f"- Identifier: {record.get('identifier') or ''}",
                f"- PDF: {record.get('pdf') or ''}",
                f"- Zotero: {record.get('zotero_key') or ''}",
                f"- BibTeX: {record.get('bibtex_key') or ''}",
                f"- Note: {md_link('note', str(record.get('_note_rel') or ''))}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        default=os.environ.get("PAPER_LIBRARY_ROOT", str(Path.home() / "paper")),
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    records = load_records(root)

    (root / "INDEX.md").write_text(build_index_md(root, records), encoding="utf-8")

    print(json.dumps({"root": str(root), "index": str(root / "INDEX.md"), "count": len(records)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
