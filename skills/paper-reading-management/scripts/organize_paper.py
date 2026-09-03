#!/usr/bin/env python3
"""Create a local reading packet for a paper."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path


CORE_FIELDS = ("topic", "problem", "method", "innovation", "significance")


def slugify(text: str, max_len: int = 80) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text.lower()).strip("-")
    slug = re.sub(r"-+", "-", slug)
    return (slug[:max_len].strip("-") or "untitled-paper")


def compact_slug(text: str, fallback: str = "") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "", text).lower()
    return cleaned or fallback


def safe_path_part(text: str) -> str:
    cleaned = re.sub(r"[/:\0]+", "-", text).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "Unfiled"


def split_collection_path(raw: str) -> list[str]:
    if not raw:
        return ["Unfiled"]
    parts = [safe_path_part(part) for part in raw.split("/") if part.strip()]
    return parts or ["Unfiled"]


def read_summary(path: str | None) -> str:
    if not path:
        return ""
    summary_path = Path(path).expanduser()
    return summary_path.read_text(encoding="utf-8")


def paper_folder_name(title: str, short_title: str, publication: str, year: str) -> str:
    title_part = slugify(short_title or title, max_len=64)
    venue_part = compact_slug(publication or year)
    return f"{title_part}--{venue_part}" if venue_part else title_part


def extract_core_content(report: str) -> dict[str, str]:
    """Extract Topic/Problem/Method/Innovation/Significance from a report."""
    core: dict[str, str] = {}
    pattern = re.compile(
        r"^\s*(?:[-*]\s*)?\*\*(Topic|Problem|Method|Innovation|Significance)\*\*"
        r"\s*(?:—|--|:|：)\s*(.+?)\s*$"
    )
    for line in report.splitlines():
        match = pattern.match(line)
        if match:
            key = match.group(1).lower()
            core.setdefault(key, match.group(2).strip())
    return core


def extract_one_sentence_summary(report: str) -> str:
    patterns = [
        r"^\s*(?:[-*]\s*)?\*\*(?:一句话总结|One-sentence summary)\*\*\s*(?:[:：])\s*(.+?)\s*$",
        r"^\s*(?:[-*]\s*)?(?:一句话总结|One-sentence summary)\s*(?:[:：])\s*(.+?)\s*$",
    ]
    for pattern in patterns:
        for line in report.splitlines():
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


def build_one_sentence_summary(metadata: dict[str, object]) -> str:
    if metadata.get("one_sentence_summary"):
        return str(metadata["one_sentence_summary"]).strip()
    core = {field: normalize_clause(metadata.get(field)) for field in CORE_FIELDS}
    if sum(1 for value in core.values() if value) < 3:
        return ""
    title = normalize_clause(metadata.get("title")) or "该论文"
    topic = core["topic"] or "目标人工智能问题"
    method = core["method"] or "一种专门方法"
    return f"{title}聚焦{topic}，并通过{method}解决相关研究问题。"


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def front_link_block(metadata: dict[str, object]) -> str:
    paper_url = metadata.get("paper_url") or metadata.get("url") or ""
    return "\n".join(
        [
            f"- Title: {metadata.get('title') or ''}",
            f"- Paper link: {paper_url}",
            f"- Web/project link: {metadata.get('web_url') or ''}",
            f"- GitHub link: {metadata.get('github_url') or ''}",
        ]
    )


def add_note_front_links(summary: str, metadata: dict[str, object]) -> str:
    block = front_link_block(metadata)
    if not summary:
        return ""
    if re.search(r"^- Title:\s*", summary, flags=re.MULTILINE):
        return summary.rstrip() + "\n"
    match = re.search(r"(?m)^##\s+0\.\s+Concise Summary\b", summary)
    if match:
        prefix = summary[: match.start()].rstrip()
        head = f"{prefix}\n\n{block}" if prefix else block
        return (head + "\n\n---\n\n" + summary[match.start() :].lstrip()).rstrip() + "\n"
    return (block + "\n\n---\n\n" + summary).rstrip() + "\n"


def build_note(metadata: dict[str, object], summary: str, prompt: str | None) -> str:
    if summary:
        return add_note_front_links(summary, metadata)
    return "\n".join(
        [
            f"# {metadata.get('title') or 'Untitled Paper'}",
            "",
            front_link_block(metadata),
            "",
            "---",
            "",
            "## 0. Concise Summary",
            "",
            "- **Topic** —",
            "- **Problem** —",
            "- **Method** —",
            "- **Innovation** —",
            "- **Significance** —",
            "- **One-sentence summary**:",
            "",
            "## 1. Motivation",
            "",
            "## 2. Innovation",
            "",
            "## 3. Main Content",
            "",
            "### 3.1 Design Architecture & Methods",
            "",
            "### 3.2 Key Algorithms & Mathematical Derivations",
            "",
            "### 3.3 Models & Training & Dataset",
            "",
            "### 3.4 Experimental Setup & Results",
            "",
            "### 3.5 Technical Details",
            "",
            "## 4. Significance and Impact",
            "",
            "## 5. Clarifications and Simplifications",
            "",
            "## 6. Additional Notes",
            "",
        ]
    )


def build_retrieval(metadata: dict[str, object]) -> str:
    release_date = metadata.get("date") or metadata.get("year") or ""
    return "\n".join(
        [
            f"# {metadata.get('short_title') or metadata.get('title') or 'Untitled Paper'}",
            "",
            front_link_block(metadata),
            "",
            "## Core Content",
            "",
            f"- **Topic**: {metadata.get('topic') or ''}",
            f"- **Problem**: {metadata.get('problem') or ''}",
            f"- **Method**: {metadata.get('method') or ''}",
            f"- **Innovation**: {metadata.get('innovation') or ''}",
            f"- **Significance**: {metadata.get('significance') or ''}",
            f"- **One-sentence summary**: {metadata.get('one_sentence_summary') or ''}",
            "",
            "## Bibliographic Metadata",
            "",
            f"- Authors: {metadata.get('authors') or ''}",
            f"- Publication: {metadata.get('publication') or metadata.get('venue') or ''}",
            f"- Date: {release_date}",
            f"- Identifier: {metadata.get('identifier') or ''}",
            f"- PDF: {metadata.get('pdf') or ''}",
            f"- Zotero: {metadata.get('zotero_key') or ''}",
            f"- BibTeX: {metadata.get('bibtex_key') or ''}",
            f"- Note: {metadata.get('note_path') or ''}",
            "",
        ]
    ).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--library-root",
        default=os.environ.get("PAPER_LIBRARY_ROOT", str(Path.home() / "paper")),
        help="Paper library root; defaults to PAPER_LIBRARY_ROOT or ~/paper",
    )
    parser.add_argument("--title", required=True)
    parser.add_argument("--short-title", default="")
    parser.add_argument("--authors", default="")
    parser.add_argument("--date", default="", help="First public release date, e.g. arXiv v1 submission date")
    parser.add_argument("--year", default="", help=argparse.SUPPRESS)
    parser.add_argument("--venue", default="")
    parser.add_argument("--publication", default="", help="Formal venue/version, e.g. CVPR 2026, NeurIPS 2025, arXiv 2024")
    parser.add_argument("--identifier", default="")
    parser.add_argument("--url", default="")
    parser.add_argument("--paper-url", default="")
    parser.add_argument("--web-url", default="")
    parser.add_argument("--github-url", default="")
    parser.add_argument("--pdf", default="", help="Existing PDF path, usually from Zotero attachment")
    parser.add_argument("--copy-pdf", action="store_true", help="Copy the PDF into the paper folder as paper.pdf")
    parser.add_argument("--zotero-key", default="")
    parser.add_argument("--bibtex-key", default="")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--keyword", action="append", default=[])
    parser.add_argument("--domain-tag", action="append", default=[], help="Domain tag, e.g. vln")
    parser.add_argument("--method-tag", action="append", default=[], help="Method tag, e.g. spatial-memory")
    parser.add_argument("--project-tag", action="append", default=[], help="Project tag, e.g. SpaceVLN-related")
    parser.add_argument("--zotero-tag", action="append", default=[], help="Lightweight Zotero-facing tag")
    parser.add_argument("--collection", action="append", default=[])
    parser.add_argument("--collection-path", default="", help="Zotero collection path, e.g. VLN/Classic")
    parser.add_argument("--status", default="read")
    parser.add_argument("--paper-type", default="")
    parser.add_argument("--topic", default="")
    parser.add_argument("--index-summary", default="", help="One concise retrieval sentence")
    parser.add_argument("--problem", default="")
    parser.add_argument("--method", default="")
    parser.add_argument("--innovation", default="")
    parser.add_argument("--significance", default="")
    parser.add_argument("--one-sentence-summary", default="", help="Concise Chinese one-sentence overview for Zotero Style remark")
    parser.add_argument("--summary", help="Markdown summary to insert into note.md")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--no-retrieval", action="store_true", help="Skip retrieval.md and keep only metadata.json plus note.md")
    parser.add_argument("--no-index", action="store_true", help="Skip updating root INDEX.md")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.library_root).expanduser().resolve()
    year = args.year or (args.date[:4] if args.date else "unknown-year")
    collection_parts = split_collection_path(args.collection_path)
    folder = root.joinpath(*collection_parts) / paper_folder_name(
        args.title, args.short_title, args.publication, year
    )
    pdf_output = ""
    note_path = str(folder / "note.md")
    retrieval_path = "" if args.no_retrieval else str(folder / "retrieval.md")

    metadata = {
        "title": args.title,
        "short_title": args.short_title,
        "authors": args.authors,
        "date": args.date,
        "year": args.year,
        "venue": args.venue,
        "publication": args.publication,
        "identifier": args.identifier,
        "url": args.url,
        "paper_url": args.paper_url,
        "web_url": args.web_url,
        "github_url": args.github_url,
        "pdf": "",
        "pdf_copied": False,
        "zotero_key": args.zotero_key,
        "bibtex_key": args.bibtex_key,
        "tags": unique(args.tag + args.domain_tag + args.method_tag + args.project_tag),
        "keywords": args.keyword,
        "domain_tags": unique(args.domain_tag),
        "method_tags": unique(args.method_tag),
        "project_tags": unique(args.project_tag),
        "zotero_tags": unique(args.zotero_tag),
        "collections": args.collection,
        "collection_path": "/".join(collection_parts),
        "status": args.status,
        "paper_type": args.paper_type,
        "topic": args.topic,
        "index_summary": args.index_summary,
        "problem": args.problem,
        "method": args.method,
        "innovation": args.innovation,
        "significance": args.significance,
        "one_sentence_summary": args.one_sentence_summary,
        "local_folder": str(folder),
        "note_path": note_path,
        "retrieval_path": retrieval_path,
        "created": date.today().isoformat(),
    }

    if args.pdf:
        pdf_path = Path(args.pdf).expanduser().resolve()
        pdf_output = str(folder / "paper.pdf") if args.copy_pdf else str(pdf_path)
        metadata["pdf"] = pdf_output
        metadata["pdf_copied"] = bool(args.copy_pdf)
        if not pdf_path.exists():
            raise SystemExit(f"PDF does not exist: {pdf_path}")

    summary_text = read_summary(args.summary)
    core = extract_core_content(summary_text)
    for field in CORE_FIELDS:
        if not metadata.get(field) and core.get(field):
            metadata[field] = core[field]
    if not metadata.get("one_sentence_summary"):
        metadata["one_sentence_summary"] = extract_one_sentence_summary(summary_text)
    if not metadata.get("one_sentence_summary"):
        metadata["one_sentence_summary"] = build_one_sentence_summary(metadata)

    if args.dry_run:
        print(json.dumps({"folder": str(folder), "metadata": metadata}, indent=2))
        return 0

    folder.mkdir(parents=True, exist_ok=True)

    if args.pdf and args.copy_pdf:
        shutil.copy2(Path(args.pdf).expanduser().resolve(), folder / "paper.pdf")

    (folder / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (folder / "note.md").write_text(
        build_note(metadata, summary_text, args.prompt),
        encoding="utf-8",
    )
    if not args.no_retrieval:
        (folder / "retrieval.md").write_text(build_retrieval(metadata), encoding="utf-8")
    if not args.no_index:
        update_index = Path(__file__).with_name("update_index.py")
        if update_index.exists():
            subprocess.run(
                [sys.executable, str(update_index), str(root)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )

    print(
        json.dumps(
            {
                "folder": str(folder),
                "note": note_path,
                "retrieval": retrieval_path,
                "index": str(root / "INDEX.md"),
                "pdf": pdf_output,
                "pdf_copied": bool(args.copy_pdf),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
