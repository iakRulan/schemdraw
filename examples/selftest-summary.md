# 自测记录（示例，非平台正式案例）

- 日期：2026-11-19
- 输入：本地构造的 5 行生物学关系材料 + 一份 3 类柱图数据
- 命令：

```bash
python3 scripts/schem.py    --case case.json --work .
python3 scripts/export.py   --work . --dpi 200
python3 scripts/validate.py --case case.json --work .
python3 scripts/report.py   --case case.json --work .
```

## 结果摘要

| 指标 | 值 |
|-|-|
| 实体 | 7 |
| 关系 | 5（activation 2、inhibition 2、containment 1） |
| 导出 | figure.pdf + figure.png（1667×876 @200dpi） |
| 校验 | `valid: true`，0 issues |

## 观察到的真实问题与修复（示例价值）

1. **实体名带标点**：`apoptosis.` / `CDKN1A.` 被当成不同实体。修复：抽取时 strip 末尾标点。
2. **图例数值比较类型不一致**：`data-value="10.0"` 与源数据 `10` 字符串不等。修复：改为数值比较。
3. **校验只打印不落盘**：修复：`validate.py` 同时写 `validation.json`，并由 `report.py` 汇总进 `result.json`。

> 本文件为**技能自测示例**，不冒充平台正式案例结果。
