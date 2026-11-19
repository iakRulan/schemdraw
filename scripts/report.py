#!/usr/bin/env python3
"""report — write result.json for a schematic run.

Usage:
    python3 report.py --case /input/case.json --work /app/work
"""
from __future__ import annotations

import argparse
import json
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
    ent = load(work / "entities.json")
    exp = load(work / "export_report.json") if (work / "export_report.json").exists() else {}
    val = load(work / "validation.json") if (work / "validation.json").exists() else {}

    case = load(Path(args.case)) if Path(args.case).is_file() else {}
    result = {
        "case_id": ent.get("case_id") or case.get("case_id"),
        "task": "editable-scientific-schematic",
        "status": "complete" if val.get("valid") and exp.get("status") == "complete" else "partial",
        "deliverables": {
            "editable_source": ent.get("svg"),
            "chart_source": ent.get("chart_svg"),
            "entities": "entities.json",
            "exports": exp.get("outputs", {}),
            "validation": "validation.json",
        },
        "counts": {
            "entities": len(ent.get("entities", [])),
            "relations": len(ent.get("relations", [])),
            "relation_counts": ent.get("relation_counts", {}),
        },
        "validation": {"valid": val.get("valid"), "issues": val.get("issues", [])},
        "uncertainty": [
            "确定性关系抽取仅覆盖显式模式；未覆盖的实体/关系需模型按材料补充并标注来源。",
            "导出依赖 LibreOffice；缺失时状态为 partial。",
        ],
        "sources": ent.get("materials", []),
        "changes": [
            {"step": "extract", "detail": f"{len(ent.get('entities', []))} entities, {len(ent.get('relations', []))} relations"},
            {"step": "export", "detail": json.dumps(exp.get("outputs", {}), ensure_ascii=False)},
            {"step": "validate", "detail": f"valid={val.get('valid')}"},
        ],
    }
    (work / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: status={result['status']} valid={val.get('valid')}")
    return result


if __name__ == "__main__":
    main()
