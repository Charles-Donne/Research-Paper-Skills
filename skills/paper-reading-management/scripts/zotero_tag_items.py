#!/usr/bin/env python3
"""Add, remove, or replace tags on Zotero local API items."""

from __future__ import annotations

import argparse
import json

from zotero_api import load_item, write_tags


def tag_names(tags: list[dict]) -> list[str]:
    names: list[str] = []
    for tag in tags:
        name = tag.get("tag")
        if name and name not in names:
            names.append(name)
    return names


def planned_tags(current: list[str], adds: list[str], removes: list[str], replacements: list[tuple[str, str]]) -> list[str]:
    result = list(current)
    for old, new in replacements:
        result = [new if tag == old else tag for tag in result]
    result = [tag for tag in result if tag not in set(removes)]
    for tag in adds:
        if tag not in result:
            result.append(tag)
    return result


def parse_replace(values: list[str]) -> list[tuple[str, str]]:
    pairs = []
    for value in values:
        if "=" not in value:
            raise SystemExit(f"--replace expects OLD=NEW, got: {value}")
        old, new = value.split("=", 1)
        if not old or not new:
            raise SystemExit(f"--replace expects non-empty OLD=NEW, got: {value}")
        pairs.append((old, new))
    return pairs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--item-key", action="append", required=True, help="Zotero item key; repeat for batches")
    parser.add_argument("--add", action="append", default=[])
    parser.add_argument("--remove", action="append", default=[])
    parser.add_argument("--replace", action="append", default=[], help="OLD=NEW; repeat as needed")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true", help="Confirm Zotero write")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    replacements = parse_replace(args.replace)
    changes = []

    for key in args.item_key:
        item = load_item(key)
        data = item.get("data", {})
        current_objects = data.get("tags") or []
        current = tag_names(current_objects)
        updated = planned_tags(current, args.add, args.remove, replacements)
        change = {
            "item_key": key,
            "title": data.get("title"),
            "version": data.get("version") or item.get("version"),
            "before": current,
            "after": updated,
            "changed": current != updated,
        }
        changes.append(change)

    if args.json or args.dry_run or not args.yes:
        print(json.dumps(changes, ensure_ascii=False, indent=2))

    if args.dry_run or not args.yes:
        return 0

    for change in changes:
        if not change["changed"]:
            continue
        write_tags(change["item_key"], change["after"])

    if not args.json:
        print(json.dumps({"updated": [c["item_key"] for c in changes if c["changed"]]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
