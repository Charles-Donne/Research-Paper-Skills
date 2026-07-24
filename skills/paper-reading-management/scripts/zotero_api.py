#!/usr/bin/env python3
"""Small shared Zotero local API helpers for paper-reading scripts."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = os.environ.get("ZOTERO_LOCAL_API_URL", "http://127.0.0.1:23119").rstrip("/")
MCP_URL = os.environ.get("ZOTERO_MCP_URL", "http://127.0.0.1:23120/mcp")
LOCAL_USER = "/api/users/0"
HEADERS = {
    "Zotero-API-Version": "3",
    "Content-Type": "application/json",
}


def item_path(item_key: str) -> str:
    return f"{LOCAL_USER}/items/{urllib.parse.quote(item_key)}"


def request(
    path: str,
    method: str = "GET",
    data: object | None = None,
    version: int | None = None,
    allow_http_error: bool = False,
) -> tuple[bool, int | None, dict[str, str], bytes]:
    headers = dict(HEADERS)
    if version is not None:
        headers["If-Unmodified-Since-Version"] = str(version)
    body = None if data is None else json.dumps(data).encode("utf-8")
    req = urllib.request.Request(BASE_URL + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return True, res.status, dict(res.headers), res.read()
    except urllib.error.HTTPError as exc:
        body = exc.read()
        if allow_http_error:
            return False, exc.code, dict(exc.headers), body
        detail = body.decode("utf-8", errors="replace")
        raise SystemExit(f"Zotero API error {exc.code} for {method} {path}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach Zotero local API at {BASE_URL}: {exc}") from exc


def load_item(item_key: str) -> dict:
    ok, status, _, body = request(item_path(item_key))
    if not ok or status != 200:
        raise SystemExit(f"Unexpected status {status} for {item_key}")
    return json.loads(body.decode("utf-8"))


def item_version(item: dict) -> int:
    data = item.get("data") or {}
    version = data.get("version") or item.get("version")
    if version is None:
        key = data.get("key") or item.get("key") or "<unknown>"
        raise SystemExit(f"Missing item version for {key}")
    return int(version)


def mcp_request(payload: dict, session_id: str | None = None) -> tuple[str | None, dict]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return res.headers.get("Mcp-Session-Id") or session_id, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Zotero MCP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Could not reach Zotero MCP at {MCP_URL}. Install and enable a Zotero MCP "
            f"write bridge, or set ZOTERO_MCP_URL. Error: {exc}"
        ) from exc


def mcp_tool_call(name: str, arguments: dict) -> dict:
    session_id, _ = mcp_request(
        {
            "jsonrpc": "2.0",
            "id": "initialize",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "paper-reading-management", "version": "1.0"},
            },
        }
    )
    _, response = mcp_request(
        {
            "jsonrpc": "2.0",
            "id": name,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        session_id,
    )
    if response.get("error"):
        raise SystemExit(f"Zotero MCP tool {name} failed: {response['error']}")
    result = response.get("result") or {}
    for part in result.get("content") or []:
        if part.get("type") != "text":
            continue
        try:
            parsed = json.loads(part.get("text") or "")
        except json.JSONDecodeError:
            continue
        if parsed.get("success") is False:
            raise SystemExit(f"Zotero MCP tool {name} failed: {parsed.get('error')}")
        return parsed
    return result


def write_metadata(item_key: str, fields: dict[str, str]) -> dict:
    return mcp_tool_call("write_metadata", {"itemKey": item_key, "fields": fields})


def write_tags(item_key: str, tags: list[str]) -> dict:
    return mcp_tool_call("write_tag", {"action": "set", "itemKey": item_key, "tags": tags})
