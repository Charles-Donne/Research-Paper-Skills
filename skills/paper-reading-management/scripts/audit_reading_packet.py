#!/usr/bin/env python3
"""Audit paper-reading packets for isolated-reading and figure/table hygiene."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_HEADINGS = [
    "## 0. Concise Summary",
    "## 1. Motivation",
    "## 2. Innovation",
    "## 3. Main Content",
    "### 3.1 Design Architecture & Methods",
    "### 3.2 Key Algorithms & Mathematical Derivations",
    "### 3.3 Models & Training & Dataset",
    "### 3.4 Experimental Setup & Results",
    "### 3.5 Technical Details",
    "## 4. Significance and Impact",
    "## 5. Clarifications and Simplifications",
    "## 6. Additional Notes",
]

FRONT_LINK_FIELDS = ["Title", "Paper link", "Web/project link", "GitHub link"]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def image_links(markdown: str) -> list[str]:
    return re.findall(r"!\[[^\]]*\]\(([^)]+)\)", markdown)


def explicit_figure_table_mentions(markdown: str) -> list[str]:
    # English labels are most common in papers; keep Chinese labels too.
    pattern = re.compile(r"\b(?:Fig\.?|Figure|Table)\s*\d+[A-Za-z]?\b|图\s*\d+|表\s*\d+", re.IGNORECASE)
    return pattern.findall(markdown)


def audit_folder(folder: Path, require_isolated: bool) -> dict:
    note_path = folder / "note.md"
    metadata_path = folder / "metadata.json"
    problems: list[str] = []
    warnings: list[str] = []

    if not note_path.exists():
        return {"folder": str(folder), "ok": False, "problems": ["missing note.md"], "warnings": warnings}

    text = note_path.read_text(encoding="utf-8")
    try:
        metadata = load_json(metadata_path)
    except (OSError, json.JSONDecodeError) as exc:
        metadata = {}
        problems.append(f"invalid metadata.json: {exc}")

    first_heading = text.find(REQUIRED_HEADINGS[0])
    front_matter = text[:first_heading] if first_heading >= 0 else ""
    front_fields = re.findall(
        r"(?m)^-\s+(Title|Paper link|Web/project link|GitHub link):",
        front_matter,
    )
    if front_fields != FRONT_LINK_FIELDS:
        problems.append(
            "front-link fields must appear exactly once and in order: "
            + ", ".join(FRONT_LINK_FIELDS)
        )

    positions = []
    for heading in REQUIRED_HEADINGS:
        pos = text.find(heading)
        if pos < 0:
            problems.append(f"missing heading: {heading}")
        positions.append(pos)
    present_positions = [pos for pos in positions if pos >= 0]
    if present_positions != sorted(present_positions):
        problems.append("required headings are out of order")

    one_sentence_count = len(re.findall(r"\*\*One-sentence summary\*\*:", text))
    if one_sentence_count != 1:
        problems.append(f"expected exactly one One-sentence summary, found {one_sentence_count}")

    unresolved = re.findall(r"<!--\s*(?:figure|table):.*?-->", text, flags=re.IGNORECASE)
    if unresolved:
        problems.append(f"unresolved figure/table markers: {len(unresolved)}")

    links = image_links(text)
    missing_images = [link for link in links if not (folder / link).exists()]
    if missing_images:
        problems.append(f"missing image files: {missing_images}")
    figures_dir = (folder / "figures").resolve()
    outside_figures = []
    for link in links:
        try:
            (folder / link).resolve().relative_to(figures_dir)
        except ValueError:
            outside_figures.append(link)
    if outside_figures:
        problems.append(f"image files outside figures/: {outside_figures}")

    mentions = explicit_figure_table_mentions(text)
    if mentions and not links:
        problems.append("note mentions figures/tables but contains no image links")
    if len(links) < len(set(mentions)) and mentions:
        warnings.append(
            f"image count ({len(links)}) is lower than unique figure/table mention count ({len(set(mentions))}); inspect manually"
        )

    page_snapshots = [link for link in links if Path(link).name.startswith("page-")]
    if page_snapshots:
        warnings.append(
            f"full-page snapshot fallbacks detected ({len(page_snapshots)}); prefer cropped figure/table regions"
        )

    if require_isolated:
        if metadata.get("reading_agent_isolated") is not True:
            problems.append("metadata.reading_agent_isolated is not true")
        if metadata.get("reading_agent_fork_context") is not False:
            problems.append("metadata.reading_agent_fork_context is not false")

    return {
        "folder": str(folder),
        "ok": not problems,
        "problems": problems,
        "warnings": warnings,
        "images": len(links),
        "mentions": len(mentions),
        "reading_agent_id": metadata.get("reading_agent_id") or "",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folders", nargs="+", help="Paper folders containing note.md")
    parser.add_argument("--require-isolated", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = [audit_folder(Path(folder).expanduser().resolve(), args.require_isolated) for folder in args.folders]
    if args.require_isolated and len(results) > 1:
        seen_agents: dict[str, str] = {}
        for result in results:
            agent_id = result.get("reading_agent_id") or ""
            if not agent_id:
                continue
            if agent_id in seen_agents:
                result["problems"].append(
                    f"reading agent {agent_id} is reused from {seen_agents[agent_id]}"
                )
                result["ok"] = False
            else:
                seen_agents[agent_id] = result["folder"]

    ok = all(result["ok"] for result in results)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for result in results:
            status = "OK" if result["ok"] else "FAIL"
            print(f"{status} {result['folder']}")
            for problem in result["problems"]:
                print(f"  problem: {problem}")
            for warning in result["warnings"]:
                print(f"  warning: {warning}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
