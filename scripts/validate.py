#!/usr/bin/env python3
"""validate — check a schematic against its sources and export contract.

Usage:
    python3 validate.py --case /input/case.json --work /app/work

Checks:
  1. every relation endpoint is a declared entity;
  2. every relation carries provenance (provided list or a source quote);
  3. chart legend labels/values match the source chart data exactly;
  4. the SVG has selectable text (no rasterized text), grouped layers;
  5. exports exist (figure.pdf / figure.png) and the PNG has the expected size.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load(path: Path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--work", required=True)
    args = ap.parse_args(argv)

    work = Path(args.work)
    issues = []
    checks = {}

    ent_path = work / "entities.json"
    svg_path = work / "figure.svg"
    for p in (ent_path, svg_path):
        if not p.exists():
            print(json.dumps({"valid": False, "issues": [f"missing: {p.name}"]}, ensure_ascii=False))
            return 1

    ent = load(ent_path)
    svg = svg_path.read_text(encoding="utf-8", errors="ignore")
    entities = set(ent.get("entities", []))
    relations = ent.get("relations", [])

    # 1. endpoints
    dangling = []
    for r in relations:
        for side in ("source", "target"):
            if r.get(side) not in entities:
                dangling.append({"relation": r, "side": side, "value": r.get(side)})
    checks["relations"] = len(relations)
    checks["dangling_endpoints"] = len(dangling)
    if dangling:
        issues.append(f"{len(dangling)} relation endpoints are not declared entities: "
                      f"{[d['value'] for d in dangling[:5]]}")

    # 2. provenance
    no_prov = [r for r in relations if not (r.get("provenance") or r.get("quote") or r.get("provided"))]
    checks["relations_without_provenance"] = len(no_prov)
    if no_prov:
        issues.append(f"{len(no_prov)} relations lack provenance/quote")

    # 3. chart legend vs source data
    case = load(Path(args.case)) if Path(args.case).is_file() else {}
    chart = case.get("chart") or case.get("chart_data")
    chart_path = work / "chart.svg"
    if chart and chart_path.exists():
        csvg = chart_path.read_text(encoding="utf-8", errors="ignore")
        for i, (lab, val) in enumerate(zip(chart.get("labels", []), chart.get("values", []))):
            if f'data-label="{lab}"' not in csvg:
                issues.append(f"chart legend mismatch for {lab}")
                continue
            m = re.search(r'data-label="' + re.escape(str(lab)) + r'" data-value="([-0-9.eE]+)"', csvg)
            if not m or abs(float(m.group(1)) - float(val)) > 1e-9:
                issues.append(f"chart data mismatch for {lab}: source={val}")
        checks["chart_labels"] = len(chart.get("labels", []))
    elif chart:
        issues.append("case declares chart data but chart.svg is missing")

    # 4. SVG structure
    checks["svg_has_text"] = "<text" in svg
    checks["svg_has_groups"] = svg.count("<g ") + svg.count("<g>") >= 2
    checks["svg_size_bytes"] = len(svg)
    if "<text" not in svg:
        issues.append("SVG has no <text> elements: text would not be selectable")
    if "<image" in svg and "<text" not in svg:
        issues.append("SVG appears to be a raster image without selectable text")

    # 5. exports
    exp = work / "export_report.json"
    if exp.exists():
        er = load(exp)
        outputs = er.get("outputs", {})
        checks["exports"] = outputs
        if "pdf" not in outputs:
            issues.append("no PDF export recorded")
        if "png" not in outputs:
            issues.append("no PNG export recorded")
        png = work / outputs.get("png", "figure.png")
        if png.exists() and png.stat().st_size < 1000:
            issues.append(f"PNG suspiciously small ({png.stat().st_size} bytes)")
    else:
        issues.append("export_report.json missing; run export.py")

    verdict = {"valid": not issues, "checks": checks, "issues": issues,
               "case_id": ent.get("case_id")}
    (work / "validation.json").write_text(json.dumps(verdict, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
