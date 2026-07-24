#!/usr/bin/env python3
"""Print Zotero collection paths for a local item key."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


BASE_URL = "http://127.0.0.1:23119"
LOCAL_USER = "/api/users/0"
HEADERS = {"Zotero-API-Version": "3"}


def api_get(path: str) -> object:
    req = urllib.request.Request(BASE_URL + path, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Zotero API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach Zotero local API at {BASE_URL}: {exc}") from exc


def collection_path(key: str, collections_by_key: dict[str, dict]) -> list[str]:
    path = []
    seen = set()
    current = key
    while current and current not in seen:
        seen.add(current)
        collection = collections_by_key.get(current)
        if not collection:
            break
        data = collection.get("data") or collection
        path.append(data.get("name") or current)
        current = data.get("parentCollection") or None
    return list(reversed(path))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("item_key")
    parser.add_argument("--first", action="store_true", help="Print the primary path only")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    item = api_get(f"{LOCAL_USER}/items/{args.item_key}")
    collection_keys = (item.get("data") or {}).get("collections") or []
    collections = api_get(f"{LOCAL_USER}/collections")
    by_key = {collection.get("key"): collection for collection in collections}
    paths = [collection_path(key, by_key) for key in collection_keys]
    paths = [path for path in paths if path] or [["Unfiled"]]
    paths.sort(key=lambda p: (-len(p), "/".join(p).lower()))

    if args.first:
        print("/".join(paths[0]))
    elif args.json:
        print(json.dumps(paths, ensure_ascii=False, indent=2))
    else:
        for path in paths:
            print("/".join(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
