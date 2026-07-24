#!/usr/bin/env python3
"""Render a PDF page or crop region as a PNG for insertion into notes."""

from __future__ import annotations

import argparse
from pathlib import Path

import pdfplumber


def parse_bbox(raw: str | None) -> tuple[float, float, float, float] | None:
    if not raw:
        return None
    parts = [float(part.strip()) for part in raw.split(",")]
    if len(parts) != 4:
        raise SystemExit("--bbox must be x0,top,x1,bottom in PDF points")
    x0, top, x1, bottom = parts
    if x1 <= x0 or bottom <= top:
        raise SystemExit("--bbox must satisfy x1 > x0 and bottom > top")
    return x0, top, x1, bottom


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--page", type=int, required=True, help="1-based page number")
    parser.add_argument("--out", required=True)
    parser.add_argument("--bbox", help="Optional crop: x0,top,x1,bottom in PDF points")
    parser.add_argument("--resolution", type=int, default=180)
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    if not pdf_path.exists():
        raise SystemExit(f"PDF does not exist: {pdf_path}")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bbox = parse_bbox(args.bbox)
    with pdfplumber.open(str(pdf_path)) as doc:
        if args.page < 1 or args.page > len(doc.pages):
            raise SystemExit(f"Page {args.page} out of range; PDF has {len(doc.pages)} pages")
        page = doc.pages[args.page - 1]
        target = page.crop(bbox) if bbox else page
        image = target.to_image(resolution=args.resolution)
        image.save(str(out_path), format="PNG")

    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
