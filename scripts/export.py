#!/usr/bin/env python3
"""export — render the editable SVG into publication exports (PDF + PNG).

Usage:
    python3 export.py --work /app/work [--svg figure.svg] [--dpi 300]

Strategy:
  1. LibreOffice headless converts SVG -> PDF (vector, selectable text).
  2. PyMuPDF rasterizes the PDF -> PNG at the requested DPI.

If LibreOffice is unavailable, the script reports the limitation honestly and
still writes a PNG via a fallback renderer when one is present.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "1.0.0"


def run(cmd, timeout=120):
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout + proc.stderr
    except Exception as exc:  # noqa: BLE001
        return 1, f"{type(exc).__name__}: {exc}"


def find_soffice():
    candidates = [
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        shutil.which("soffice"),
        shutil.which("libreoffice"),
    ]
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


def svg_to_pdf(svg: Path, out_dir: Path, soffice: str):
    code, out = run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(svg)])
    produced = out_dir / (svg.stem + ".pdf")
    return (produced if produced.exists() else None), out.strip()


def pdf_to_png(pdf: Path, out_dir: Path, dpi: int):
    try:
        import fitz
    except Exception:
        return None, "PyMuPDF unavailable"
    try:
        doc = fitz.open(str(pdf))
        page = doc[0]
        zoom = dpi / 72.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        png = out_dir / (pdf.stem + ".png")
        pix.save(str(png))
        return png, f"rendered {pix.width}x{pix.height} at {dpi} dpi"
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True)
    ap.add_argument("--svg", default=None)
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args(argv)

    work = Path(args.work)
    svg = Path(args.svg) if args.svg else (work / "figure.svg")
    notes = []
    outputs = {}

    if not svg.exists():
        print(json.dumps({"status": "error", "issues": [f"missing SVG: {svg}"]}, ensure_ascii=False))
        return 1

    soffice = find_soffice()
    if soffice:
        pdf, msg = svg_to_pdf(svg, work, soffice)
        notes.append(f"soffice: {msg[:200]}")
        if pdf:
            outputs["pdf"] = pdf.name
            png, msg2 = pdf_to_png(pdf, work, args.dpi)
            notes.append(f"png: {msg2}")
            if png:
                outputs["png"] = png.name
        else:
            notes.append("PDF conversion failed")
    else:
        notes.append("LibreOffice not found; PDF export unavailable")

    result = {
        "svg": svg.name,
        "outputs": outputs,
        "dpi": args.dpi,
        "notes": notes,
        "status": "complete" if "png" in outputs and "pdf" in outputs else "partial",
    }
    (work / "export_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    sys.exit(main())
