# Stage 3：意见聚合与二稿路线图

读取 A/B/C 的 JSON 与 `stage1/linter.json`，填写 `consolidator.json`，然后运行：

```bash
python scripts/thesis_review.py render runs/<id>
```

## 规则

- 去重：同一根因只保留一条 Major，附上所有定位。
- 机械预检中的未定义符号默认 Minor；若导致损失不可解释则升 Major。
- 缺消融、缺问题形式化、无对照基线 → Major。
- 定级只能是：优秀 / 良好 / 及格 / 退修。
- 机械预检单独不得给「优秀」。
- 每条 Major 必须能映射到路线图中的一条可执行步骤。
- 读 Agent C 的 `code_correspondence`（四个维度：数字 / 结构 / 超参 / 设计）。`mismatch` 去重后写入 Major，路线图的实验项写明要改的表和文件。结构或实验设计对不上一律 Major；超参不一致默认 Major（破坏可复现性），仅打印/记录性偏差可 Minor。
- `aspects_skipped` 里的维度只是写明了跳过理由，不代表已核验；总体评价与 Major 不得把跳过项写成已复核。
- `code_status` 为 `missing` 或 `partial` 时，未核对的主张不得写成已复核。
- 把 `status` 改为 `done` 之前，`code_status` 必须是 `missing`、`partial` 或 `checked`，且数字/结构/超参/设计四个维度均有对账行或跳过理由（`doctor` 会检查）。没有该字段的历史 run 不追溯。

## 深审完成标记与预检对账

- 深审结束把 `status` 从 `pending` 改为 `done`。`done` 之后 `majors` / `minors`
  为空列表即表示「深审确认无」，render 不再回退到机械预检兜底。
- 对 Stage 1 的每条结构缺口（`stage1/linter.json` 的 `structure_gaps`），逐项
  写入 `linter_triage`：确认属实填 `accept`；属关键词误报填 `reject` 并给出
  依据（如「5.1 已给出输入/输出定义」）。`reject` 项不得以任何形式进入 Major。
- 示例：

```json
"linter_triage": [
  {"key": "problem_formulation", "verdict": "reject", "reason": "5.1 已定义输入输出与符号表，docx 抽取丢失写法所致。"},
  {"key": "related_work", "verdict": "accept", "reason": "1.3 综述仍偏罗列，保留 Major。"}
]
```
