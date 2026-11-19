---
name: schemdraw
description: "Generate editable, source-traceable scientific schematics and charts: extract entities and directed relations from the material, draw them as a layered SVG with selectable text, map chart legend/colours to the source data, export PDF + PNG at journal resolution, and validate that every element traces back to the source. Trigger on: '科研绘图', '示意图', '机制图', '流程图', '画图', 'scientific figure', 'schematic', 'mechanism figure', 'editable figure', '导出图'. Not for: statistical analysis, poster/cover layout, artistic illustration, or paper writing."
---

# schemdraw — Editable Scientific Schematics with Source Traceability

Produce a figure that is **correct, editable and export-compliant**: every entity/relation traces to the material, the legend matches the data, the text stays selectable, and the exports meet the target resolution. The failure mode this skill exists to prevent: a pretty picture with wrong entity relations, invented gene names or concentrations, a legend that disagrees with the data, and a bitmap-only output that cannot be edited.

**Method in one line:** extract entities/relations from the material → lay them out as a layered SVG (grouped, selectable text, arrow direction by relation type) → build the chart from the same source data with an explicit legend/colour map → export PDF+PNG → validate traceability and export contract.

## When to use

- Input: a case file (default `/input/case.json`) with the scientific material, optional entity/relation lists, chart data and export specs.
- Output: under `/app/output` — `figure.svg`, `chart.svg`, `figure.pdf`, `figure.png`, `entities.json`, `export_report.json`, `validation.json`, `result.json`.
- SVG is the editable source; PDF/PNG are exports.

## Pipeline (run in order)

### Phase 1 — Extract and draw

```bash
python3 scripts/schem.py --case /input/case.json --work /app/work
```

- Reads each material (text/Markdown), merges provided `entities`/`relations` with relations extracted from patterns: `X activates|promotes|enhances Y`, `X inhibits|suppresses|blocks Y`, `X -> Y`, `X --| Y`, `X binds|interacts with Y`, `X contains|includes Y`.
- Every relation carries `provenance` (`text-pattern` + the source quote) or comes from the provided list.
- Writes `entities.json` and a layered `figure.svg`: `<g id="arrows">` with `data-source`/`data-target`/`data-type`, `<g id="nodes">` with one group per entity and `<text>` labels. Arrow colour/dash encodes relation type (green = activation, red = inhibition, dashed = containment).
- If the case has chart data, writes `chart.svg` whose bars carry `data-label`/`data-value` and whose legend uses the same palette index as the bars.

### Phase 2 — Export

```bash
python3 scripts/export.py --work /app/work --dpi 300
```

LibreOffice headless converts SVG → PDF (vector, selectable text); PyMuPDF rasterizes PDF → PNG at the requested DPI. Writes `export_report.json`. If LibreOffice is missing, the report says so and the status becomes `partial` — never a silent failure.

### Phase 3 — Validate

```bash
python3 scripts/validate.py --case /input/case.json --work /app/work
```

Checks:
1. every relation endpoint is a declared entity (no dangling arrows);
2. every relation has provenance or a source quote;
3. chart legend labels and values match the source data exactly;
4. the SVG has `<text>` (selectable) and ≥2 layers;
5. PDF and PNG exports exist and the PNG is not suspiciously small.

### Phase 4 — Copy deliverables

```bash
mkdir -p /app/output
cp /app/work/figure.svg /app/work/chart.svg /app/work/figure.pdf /app/work/figure.png \
   /app/work/entities.json /app/work/export_report.json /app/work/result.json /app/output/
# validation.json is written by validate.py; copy it too if present
```

## Rules that must hold

1. **Entities come from the material.** No invented gene names, concentrations or time points; anything the model adds must be sourced and marked.
2. **Relation direction is data.** `A activates B` is drawn A → B, never reversed; the arrow type follows the relation type.
3. **Legend ⇄ data consistency.** Legend labels and colours come from the same array as the bars; changing the data changes the legend.
4. **Editable source + compliant export.** Always deliver the SVG (editable) and the PDF/PNG (export) together.
5. **Export is checked, not assumed.** DPI, font embedding and file existence are recorded; a failed export is reported.

## Exception handling

| Situation | Behaviour |
|-|-|
| No material / empty | empty entity list; SVG still written with a title |
| Relation endpoint unknown | kept in `entities` (added from the pattern) and drawn |
| Chart data missing | `chart.svg` skipped; `entities.json.chart_svg = null` |
| LibreOffice missing | PDF/PNG missing, `export_report.status = partial`, limitation recorded |
| No relations | SVG with nodes only; validation notes 0 relations |

## Self-check

```bash
python3 scripts/validate.py --case /input/case.json --work /app/work
python3 -c "import json;e=json.load(open('/app/work/entities.json'));print(len(e['entities']), len(e['relations']), e['relation_counts'])"
```

`valid: true` is required; the model must fill in any entity/relation the deterministic extractor missed, always with a source.
