# 输出字段字典

## `entities.json`

| 字段 | 说明 |
|-|-|
| `case_id` | 输入标识 |
| `materials[]` | 使用的材料标识 |
| `entities[]` | 实体名列表 |
| `relations[]` | `source` / `target` / `type` / `provenance` / `quote` |
| `relation_counts{}` | 按类型计数 |
| `svg` / `chart_svg` | 源文件名（可为 null） |
| `export_specs{}` | 导出参数 |
| `script_version` | 版本 |

## `figure.svg` / `chart.svg`

- 分层：`<g id="arrows">`、`<g id="nodes">`、`<g id="bars">`、`<g id="legend">`
- 每条边：`data-source` / `data-target` / `data-type`
- 每根柱：`data-label` / `data-value`
- 文字以 `<text>` 存在（可选择、可编辑）

## `export_report.json`

`{svg, outputs{pdf,png}, dpi, notes[], status}`

## `validation.json`

`{valid, checks, issues[], case_id}`。checks 含：`relations`、`dangling_endpoints`、`relations_without_provenance`、`chart_labels`、`svg_has_text`、`svg_has_groups`、`svg_size_bytes`、`exports`。

## `result.json`

| 字段 | 说明 |
|-|-|
| `case_id` / `task` / `status` | `editable-scientific-schematic` |
| `deliverables` | `editable_source` / `chart_source` / `entities` / `exports` / `validation` |
| `counts` | `entities` / `relations` / `relation_counts` |
| `validation` | `{valid, issues}` |
| `uncertainty` | 限制（关系抽取范围、导出依赖） |
| `sources` / `changes` | |
