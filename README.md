# schemdraw — 科研示意图生成与编辑 Skill

生成**正确、可编辑、导出合规**的科研示意图：每个实体/关系可追溯到来源材料，图例与数据逐项一致，文字保持可选，源文件与导出件同时交付。

## 解决什么问题

普通 Agent 的常见失败：把机制图当配图；实体画错（抑制画成激活、上下游颠倒）；图中出现材料里不存在的基因名/浓度/时间点；图例与数据表对不上；只出位图，文字不可选、图层不可拆；导出分辨率/字体/线宽不满足期刊要求。

## 安装与依赖

- Python 3.9+
- LibreOffice（SVG→PDF）+ PyMuPDF（PDF→PNG）；缺失时状态降为 `partial` 并记录
- 无需联网

```
schemdraw/
├── SKILL.md
├── README.md
├── GITHUB_URL.txt
├── references/
│   ├── relations-and-layout.md
│   └── output-schema.md
├── examples/
│   ├── case.example.json
│   └── selftest-summary.md
└── scripts/
    ├── schem.py       # 抽取实体/关系 + 生成 SVG
    ├── export.py      # SVG -> PDF -> PNG
    ├── validate.py    # 可追溯性与导出契约校验
    └── report.py      # result.json
```

## 用法（最小示例）

```bash
python3 scripts/schem.py    --case /input/case.json --work /app/work
python3 scripts/export.py   --work /app/work --dpi 300
python3 scripts/validate.py --case /input/case.json --work /app/work
python3 scripts/report.py   --case /input/case.json --work /app/work
```

输入示例：

```json
{
  "case_id": "demo",
  "materials": ["material.txt"],
  "export": {"width_px": 800, "height_px": 420, "dpi": 200},
  "chart": {"title": "Expression", "labels": ["A", "B", "C"], "values": [10, 20, 15]}
}
```

> 以上为**示意示例**，不是正式案例结果。

## 输出

| 文件 | 内容 |
|-|-|
| `figure.svg` | 可编辑关系图（分层、文字可选、箭头方向编码关系类型） |
| `chart.svg` | 数据图（bar 带 `data-label`/`data-value`，图例同源） |
| `figure.pdf` / `figure.png` | 导出件（300 dpi 起） |
| `entities.json` | 实体、关系、类型统计、来源清单 |
| `export_report.json` | 导出参数与结果 |
| `validation.json` | 校验判决 |
| `result.json` | `case_id` / `status` / counts / deliverables / uncertainty |

## 关键设计

- **可追溯**：每条关系带来源引文；实体来自材料或显式清单。
- **结构正确**：激活/抑制/包含用颜色与线型区分，方向由关系决定。
- **图例一致**：图例与柱子共用同一数据数组。
- **可编辑 + 合规导出**：SVG 源文件 + PDF/PNG 导出件同时交付。
- **校验而非假设**：`validate.py` 检查端点、出处、图例数据一致性、可编辑性与导出存在性。

## 局限

- 布局为确定性网格/圆周，复杂层级需人工微调；
- 关系抽取为模式匹配，隐含关系需模型补充并标注来源；
- 导出依赖 LibreOffice。

## 许可与版本

- 版本：schemdraw 1.0.0
- 依赖：Python 3.9+；LibreOffice、PyMuPDF（导出）。
