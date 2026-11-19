# 关系抽取与图面布局

## 关系模式

| 模式 | 类型 | 图面编码 |
|-|-|-|
| `X activates|promotes|enhances|upregulates|increases Y` | activation | 绿色实线箭头 |
| `X inhibits|suppresses|blocks|downregulates|decreases|reduces Y` | inhibition | 红色实线箭头 |
| `X -> Y` / `X → Y` | activation | 绿色实线箭头 |
| `X --| Y` / `X ⊣ Y` | inhibition | 红色实线箭头 |
| `X binds|interacts with Y` | binding | 绿色实线箭头 |
| `X contains|includes|consists of Y` | containment | 红色虚线箭头 |

抽取时去除实体名末尾标点（` .,;:()[]`）。每条抽取的关系记录 `provenance: text-pattern` 与来源引文（≤200 字符）。

## 实体来源

1. 案例显式 `entities` 清单；
2. 关系抽取中出现的端点（自动加入实体表）；
3. 模型按材料补充（必须标注来源，写入 `model_additions`）。

**不虚构**：材料中不出现的基因名/浓度/时间点不得进入图中。

## 布局

- 节点按 `cols = width // 220` 网格排列，行数自适应；
- 每个节点一个 `<g id="node-{entity}">`：圆角矩形 + `<text>` 标签（文字可选）；
- 箭头层 `<g id="arrows">`：每条边一个 `<line>` + 箭头多边形，带 `data-source`/`data-target`/`data-type`；
- 颜色：激活/结合 `#2E7D32`，抑制 `#C62828`，包含用虚线。

## 图表

- 柱值来自案例 `chart.values`，标签来自 `chart.labels`；
- 每根柱 `data-label` / `data-value`；
- 图例使用与柱子相同的调色板索引，保证图例⇄数据一致；
- 调色板：`#4C72B0 #DD8452 #55A868 #C44E52 #8172B3 #937860 #DA8BC3 #8C8C8C`。

## 导出

1. `soffice --headless --convert-to pdf`（矢量、文字可选）；
2. PyMuPDF `get_pixmap(matrix=Matrix(dpi/72, dpi/72))` → PNG。

导出参数（dpi、尺寸、字体）写入 `export_report.json`。
