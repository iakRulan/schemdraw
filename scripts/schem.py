#!/usr/bin/env python3
"""schem — build an editable, source-traceable relationship schematic (+ chart).

Usage:
    python3 schem.py --case /input/case.json --work /app/work

Reads the case's scientific material, extracts entities and directed relations,
maps them to a layered SVG (selectable text, grouped elements), optionally adds
a chart whose legend/colour mapping comes from the same source data, and writes
entities.json + figure.svg + result inputs.

The SVG is the editable source; export to PDF/PNG is done by export.py.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

VERSION = "1.0.0"

RELATION_PATTERNS = [
    (r"([A-Za-z0-9_\-\.]+)\s+(?:activates?|promotes?|enhances?|upregulates?|increases?)\s+(?:the\s+)?([A-Za-z0-9_\-\.]+)", "activation"),
    (r"([A-Za-z0-9_\-\.]+)\s+(?:inhibits?|suppresses?|blocks?|downregulates?|decreases?|reduces?)\s+(?:the\s+)?([A-Za-z0-9_\-\.]+)", "inhibition"),
    (r"([A-Za-z0-9_\-\.]+)\s*(->|→|-->|⟶)\s*([A-Za-z0-9_\-\.]+)", "activation"),
    (r"([A-Za-z0-9_\-\.]+)\s*(--|⊣|---|⟞)\s*([A-Za-z0-9_\-\.]+)", "inhibition"),
    (r"([A-Za-z0-9_\-\.]+)\s+(?:binds?|interacts?\s+with)\s+(?:the\s+)?([A-Za-z0-9_\-\.]+)", "binding"),
    (r"([A-Za-z0-9_\-\.]+)\s+(?:contains?|includes?|consists?\s+of)\s+(?:the\s+)?([A-Za-z0-9_\-\.]+)", "containment"),
]


def load(path: Path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def load_case(case_path: Path) -> dict:
    case_path = Path(case_path)
    if case_path.is_dir():
        return {"case_id": case_path.name, "materials": [], "raw": {}}
    raw = load(case_path)
    case = dict(raw) if isinstance(raw, dict) else {"value": raw}
    materials = (case.get("materials") or case.get("sources") or case.get("documents")
                 or case.get("files") or case.get("inputs") or [])
    if isinstance(materials, str):
        materials = [materials]
    entities = case.get("entities") or case.get("entity_list") or []
    relations = case.get("relations") or case.get("edges") or []
    chart = case.get("chart") or case.get("chart_data") or None
    specs = case.get("export") or case.get("journal_specs") or case.get("specs") or {}
    return {
        "case_id": case.get("case_id") or case.get("id") or case_path.stem,
        "raw": case,
        "materials": materials,
        "entities": entities if isinstance(entities, list) else [],
        "relations": relations if isinstance(relations, list) else [],
        "chart": chart if isinstance(chart, dict) else None,
        "specs": specs if isinstance(specs, dict) else {},
        "notes": case.get("notes") or "",
    }


def read_material(rec, base: Path):
    if isinstance(rec, str):
        rec = {"path": rec}
    path = rec.get("path") or rec.get("file")
    if not path:
        return rec.get("id") or "material", ""
    p = Path(path)
    if not p.is_absolute():
        cand = base / p
        p = cand if cand.exists() else Path(path)
    if p.exists() and p.is_file():
        return rec.get("id") or p.stem, p.read_text(encoding="utf-8", errors="ignore")
    return rec.get("id") or str(p), ""


def extract_entities_relations(text, provided_entities, provided_relations):
    """Merge provided lists with text-derived relations; record provenance."""
    prov_e = {str(e) for e in provided_entities} if provided_entities else set()
    prov_r = {(str(r.get("source")), str(r.get("target")), str(r.get("type"))) for r in provided_relations} if provided_relations else set()

    entities = list(prov_e)
    relations = [dict(r) for r in provided_relations] if provided_relations else []

    for line in text.splitlines():
        for pat, rtype in RELATION_PATTERNS:
            for m in re.finditer(pat, line):
                a, b = m.group(1).strip(" .,;:()[]"), m.group(2).strip(" .,;:()[]")
                for e in (a, b):
                    if e not in entities:
                        entities.append(e)
                key = (a, b, rtype)
                if key not in prov_r and (a, b, rtype) not in {(r.get("source"), r.get("target"), r.get("type")) for r in relations}:
                    relations.append({"source": a, "target": b, "type": rtype,
                                      "provenance": "text-pattern", "quote": line.strip()[:200]})
    return entities, relations


# -- SVG generation ---------------------------------------------------------

PALETTE = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860", "#DA8BC3", "#8C8C8C"]


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def build_svg(entities, relations, specs, case_id):
    width = int(specs.get("width_px") or 900)
    height = int(specs.get("height_px") or max(360, 120 + 90 * max(1, len(entities))))
    font = specs.get("font") or "Helvetica, Arial, sans-serif"

    # simple layered layout: containment groups not handled; place nodes on a circle/grid
    n = max(1, len(entities))
    cols = max(1, int(width // 220))
    rows = max(1, (n + cols - 1) // cols)
    pos = {}
    for i, e in enumerate(entities):
        r, c = divmod(i, cols)
        x = 120 + c * ((width - 240) / max(1, cols - 1)) if cols > 1 else width / 2
        y = 90 + r * ((height - 180) / max(1, rows - 1)) if rows > 1 else height / 2
        pos[e] = (int(x), int(y))

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{_esc(font)}">',
        f'  <title>{_esc(case_id)} relationship schematic</title>',
        '  <g id="arrows" fill="none" stroke="#333" stroke-width="1.5">',
    ]
    for r in relations:
        a, b = r.get("source"), r.get("target")
        if a not in pos or b not in pos:
            continue
        x1, y1 = pos[a]
        x2, y2 = pos[b]
        color = "#2E7D32" if r.get("type") in {"activation", "binding"} else "#C62828"
        dash = ' stroke-dasharray="4 3"' if r.get("type") == "containment" else ""
        parts.append(f'    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}"{dash} '
                     f'data-source="{_esc(a)}" data-target="{_esc(b)}" data-type="{_esc(r.get("type"))}"/>')
        parts.append(f'    <polygon points="{_arrow_head(x1, y1, x2, y2)}" fill="{color}"/>')
    parts.append('  </g>')
    parts.append('  <g id="nodes" font-size="13" text-anchor="middle">')
    for i, e in enumerate(entities):
        x, y = pos[e]
        color = PALETTE[i % len(PALETTE)]
        parts.append(f'    <g id="node-{_esc(e)}">')
        parts.append(f'      <rect x="{x-52}" y="{y-16}" width="104" height="32" rx="6" '
                     f'fill="{color}" fill-opacity="0.15" stroke="{color}"/>')
        parts.append(f'      <text x="{x}" y="{y+5}" fill="#111">{_esc(e)}</text>')
        parts.append('    </g>')
    parts.append('  </g>')
    parts.append('</svg>')
    return "\n".join(parts)


def _arrow_head(x1, y1, x2, y2, size=8):
    import math
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    px, py = x2 - ux * 16, y2 - uy * 16
    ax, ay = px - uy * size * 0.5, py + ux * size * 0.5
    bx, by = px + uy * size * 0.5, py - ux * size * 0.5
    return f"{x2},{y2} {ax:.1f},{ay:.1f} {bx:.1f},{by:.1f}"


def build_chart_svg(chart, specs):
    """A minimal, data-driven chart as SVG with a legend mapped to source data."""
    title = chart.get("title") or "chart"
    labels = [str(x) for x in (chart.get("labels") or [])]
    values = [float(v) for v in (chart.get("values") or [])]
    if not labels or not values or len(labels) != len(values):
        return None
    width = int(specs.get("width_px") or 600)
    height = int(specs.get("height_px") or 400)
    font = specs.get("font") or "Helvetica, Arial, sans-serif"
    vmax = max(values) or 1
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}" font-family="{_esc(font)}">',
             f'  <title>{_esc(title)}</title>',
             f'  <text x="{width/2}" y="24" text-anchor="middle" font-size="15">{_esc(title)}</text>',
             '  <g id="bars">']
    n = len(values)
    slot = (width - 120) / max(1, n)
    for i, (lab, val) in enumerate(zip(labels, values)):
        h = (val / vmax) * (height - 140)
        x = 60 + i * slot + slot * 0.15
        w = slot * 0.7
        y = height - 70 - h
        color = PALETTE[i % len(PALETTE)]
        parts.append(f'    <rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{color}" '
                     f'data-label="{_esc(lab)}" data-value="{val}"/>')
        parts.append(f'    <text x="{x+w/2:.1f}" y="{height-50}" text-anchor="middle" font-size="11">{_esc(lab)}</text>')
        parts.append(f'    <text x="{x+w/2:.1f}" y="{y-6:.1f}" text-anchor="middle" font-size="11">{val}</text>')
    parts.append('  </g>')
    parts.append('  <g id="legend" font-size="11">')
    for i, lab in enumerate(labels):
        lx = 60 + i * 130
        ly = height - 24
        parts.append(f'    <rect x="{lx}" y="{ly-9}" width="12" height="12" fill="{PALETTE[i % len(PALETTE)]}"/>')
        parts.append(f'    <text x="{lx+18}" y="{ly}">{_esc(lab)}</text>')
    parts.append('  </g>')
    parts.append('</svg>')
    return "\n".join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True)
    ap.add_argument("--work", required=True)
    args = ap.parse_args(argv)

    case = load_case(Path(args.case))
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    base = Path(args.case).parent if Path(args.case).is_file() else Path(args.case)

    text_parts = []
    mat_ids = []
    for rec in case["materials"]:
        mid, text = read_material(rec, base)
        mat_ids.append(mid)
        text_parts.append(text)
    text = "\n".join(text_parts)

    entities, relations = extract_entities_relations(text, case["entities"], case["relations"])
    svg = build_svg(entities, relations, case["specs"], case["case_id"])
    (work / "figure.svg").write_text(svg, encoding="utf-8")

    chart_svg = None
    if case["chart"]:
        chart_svg = build_chart_svg(case["chart"], case["specs"])
        if chart_svg:
            (work / "chart.svg").write_text(chart_svg, encoding="utf-8")

    entities_out = {
        "case_id": case["case_id"],
        "materials": mat_ids,
        "entities": entities,
        "relations": relations,
        "relation_counts": {t: sum(1 for r in relations if r.get("type") == t)
                            for t in sorted({r.get("type") for r in relations})},
        "svg": "figure.svg",
        "chart_svg": "chart.svg" if chart_svg else None,
        "export_specs": case["specs"],
        "script_version": VERSION,
    }
    save(work / "entities.json", entities_out)
    print(f"schem: {len(entities)} entities, {len(relations)} relations -> {work / 'figure.svg'}")
    return entities_out


if __name__ == "__main__":
    main()
