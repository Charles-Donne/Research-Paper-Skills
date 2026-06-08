#!/usr/bin/env python3
"""Print local PDF attachment paths for a Zotero item key."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import unquote, urlparse
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


def file_url_to_path(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "file":
        return url
    return unquote(parsed.path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("item_key", help="Top-level Zotero item key")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--first", action="store_true", help="Print only the first PDF path")
    args = parser.parse_args()

    children = api_get(f"{LOCAL_USER}/items/{args.item_key}/children")
    pdfs = []
    for child in children:
        data = child.get("data") or {}
        links = child.get("links") or {}
        enclosure = links.get("enclosure") or {}
        content_type = data.get("contentType") or enclosure.get("type") or ""
        href = enclosure.get("href") or ""
        if content_type == "application/pdf" and href:
            path = file_url_to_path(href)
            pdfs.append(
                {
                    "attachment_key": child.get("key"),
                    "title": data.get("title"),
                    "path": path,
                    "exists": Path(path).exists() if path.startswith("/") else False,
                    "url": data.get("url") or "",
                }
            )

    if args.first:
        print(pdfs[0]["path"] if pdfs else "")
        return 0 if pdfs else 1
    if args.json:
        print(json.dumps(pdfs, ensure_ascii=False, indent=2))
    else:
        for pdf in pdfs:
            exists = "exists" if pdf["exists"] else "missing"
            print(f"{pdf['attachment_key']}\t{exists}\t{pdf['path']}")
    return 0 if pdfs else 1


if __name__ == "__main__":
    raise SystemExit(main())
