#!/usr/bin/env python3
"""Audit paper-reading packets for isolated reading and manual figure/table markers."""

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


MENTION_PATTERN = re.compile(
    r"\b(?P<english>Fig\.?|Figure|Table)\s*(?P<english_number>\d+[A-Za-z]?)\b|(?P<chinese>图|表)\s*(?P<chinese_number>\d+[A-Za-z]?)",
    re.IGNORECASE,
)
MARKER_PATTERN = re.compile(
    r"<!--\s*(?P<kind>figure|table)\s*:\s*"
    r"(?P<label>(?:Fig\.?|Figure|Table)\s*\d+[A-Za-z]?)\s*-->",
    re.IGNORECASE,
)


def canonical_label(label: str) -> str:
    """Normalize English/Chinese figure-table labels for matching."""
    match = MENTION_PATTERN.search(label)
    if not match:
        return ""
    if match.group("english"):
        kind = "table" if match.group("english").lower() == "table" else "figure"
        number = match.group("english_number")
    else:
        kind = "figure" if match.group("chinese") == "图" else "table"
        number = match.group("chinese_number")
    return f"{kind}:{number.lower()}"


def explicit_figure_table_mentions(markdown: str) -> set[str]:
    return {canonical_label(match.group(0)) for match in MENTION_PATTERN.finditer(markdown)} - {""}


def marker_labels(markdown: str) -> dict[str, str]:
    markers: dict[str, str] = {}
    for match in MARKER_PATTERN.finditer(markdown):
        label = canonical_label(match.group("label"))
        if not label:
            continue
        markers[label] = match.group("kind").lower()
    return markers


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

    one_sentence_pattern = r"(?m)^\s*(?:[-*]\s*)?\*\*One-sentence summary\*\*\s*[:：]"
    one_sentence_count = len(re.findall(one_sentence_pattern, text, flags=re.IGNORECASE))
    if one_sentence_count != 1:
        problems.append(f"expected exactly one One-sentence summary line, found {one_sentence_count}")
    else:
        summary_start = text.find("## 0. Concise Summary")
        summary_end = text.find("## 1. Motivation")
        summary_section = text[summary_start:summary_end] if summary_start >= 0 and summary_end > summary_start else ""
        if not re.search(one_sentence_pattern, summary_section, flags=re.IGNORECASE):
            problems.append("One-sentence summary must be under 0. Concise Summary")

    mentions = explicit_figure_table_mentions(text)
    markers = marker_labels(text)
    embedded_images = re.findall(r"!\[[^\]]*\]\([^)]+\)", text)
    if embedded_images:
        problems.append(f"note contains Markdown image embeds ({len(embedded_images)})")

    for label in sorted(mentions):
        marker_kind = markers.get(label)
        if not marker_kind:
            problems.append(f"missing manual insertion marker for {label}")
            continue
        expected_kind = "figure" if label.startswith("figure:") else "table"
        if marker_kind != expected_kind:
            problems.append(f"wrong marker kind for {label}: {marker_kind}")

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
        "markers": len(markers),
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
