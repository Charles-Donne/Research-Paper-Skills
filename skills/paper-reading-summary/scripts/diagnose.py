#!/usr/bin/env python3
"""Diagnose the paper-reading-summary local pipeline without writing data."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
ZOTERO_BASE_URL = os.environ.get("ZOTERO_LOCAL_API_URL", "http://127.0.0.1:23119").rstrip("/")
ZOTERO_MCP_URL = os.environ.get("ZOTERO_MCP_URL", "http://127.0.0.1:23120/mcp")


def command_result(args: list[str], timeout: int = 10) -> dict:
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip()[:1200],
            "stderr": proc.stderr.strip()[:1200],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def check_python_package(name: str) -> dict:
    spec = importlib.util.find_spec(name)
    return {"ok": spec is not None, "name": name, "origin": spec.origin if spec else ""}


def check_zotero() -> dict:
    try:
        req = Request(f"{ZOTERO_BASE_URL}/api/users/0/items?limit=1", headers={"Zotero-API-Version": "3"})
        with urlopen(req, timeout=5) as res:
            return {"ok": 200 <= res.status < 300, "status": res.status, "base_url": ZOTERO_BASE_URL}
    except Exception as exc:
        return {"ok": False, "base_url": ZOTERO_BASE_URL, "error": str(exc)}


def check_zotero_mcp() -> dict:
    payload = {
        "jsonrpc": "2.0",
        "id": "initialize",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "paper-reading-summary-diagnose", "version": "1.0"},
        },
    }
    try:
        req = Request(
            ZOTERO_MCP_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=5) as res:
            body = json.loads(res.read().decode("utf-8"))
            return {
                "ok": 200 <= res.status < 300 and "result" in body,
                "status": res.status,
                "url": ZOTERO_MCP_URL,
            }
    except Exception as exc:
        return {"ok": False, "url": ZOTERO_MCP_URL, "error": str(exc)}


def parse_jsonish(stdout: str) -> dict:
    start = stdout.find("{")
    if start == -1:
        return {}
    try:
        return json.loads(stdout[start:])
    except json.JSONDecodeError:
        return {}


def check_lark() -> dict:
    lark_path = shutil.which("lark-cli")
    if not lark_path:
        return {"ok": False, "error": "lark-cli not found"}
    version = command_result(["lark-cli", "--version"])
    auth = command_result(["lark-cli", "auth", "status"], timeout=15)
    auth_data = parse_jsonish(auth.get("stdout", ""))
    identities = auth_data.get("identities") or {}
    return {
        "ok": bool(version["ok"] and auth["ok"]),
        "path": lark_path,
        "version": version.get("stdout") or "",
        "auth": {
            "ok": auth.get("ok", False),
            "brand": auth_data.get("brand") or "",
            "bot_status": (identities.get("bot") or {}).get("status") or "",
            "user_status": (identities.get("user") or {}).get("status") or "",
        },
    }


def check_organizer() -> dict:
    summary = SCRIPT_DIR.parent / "references" / "reading-output-template.md"
    return command_result(
        [
            sys.executable,
            str(SCRIPT_DIR / "organize_paper.py"),
            "--library-root",
            "/tmp/paper-reading-diagnose",
            "--title",
            "Diagnose Paper",
            "--date",
            "2026-01-01",
            "--collection-path",
            "Diagnose/Test",
            "--short-title",
            "Diagnose Paper",
            "--summary",
            str(summary),
            "--dry-run",
        ]
    )


def main() -> int:
    checks = {
        "python": {"ok": True, "version": sys.version.split()[0], "executable": sys.executable},
        "scripts": {
            "ok": all((SCRIPT_DIR / name).exists() for name in [
                "organize_paper.py",
                "feishu_sync.py",
                "zotero_sync_note.py",
                "zotero_tag_items.py",
                "pdf_figure_snapshot.py",
            ]),
            "dir": str(SCRIPT_DIR),
        },
        "organizer_dry_run": check_organizer(),
        "zotero_local_api": check_zotero(),
        "zotero_mcp_write_bridge": check_zotero_mcp(),
        "lark_cli": check_lark(),
        "pdfplumber": check_python_package("pdfplumber"),
        "pypdf": check_python_package("pypdf"),
    }
    required = ("python", "scripts", "organizer_dry_run", "zotero_local_api")
    checks["ok"] = all(checks[key].get("ok", False) for key in required)
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0 if checks["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
