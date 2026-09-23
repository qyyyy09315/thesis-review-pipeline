# Agent C：实证充分度与数据可信度审查

填写 `agent_c_experiments.json`。重点实验与分析章，并核对方法章的结构描述与训练设置。

## 必查

1. 数据集规模、划分、预处理是否可复现？
2. 基线是否代表近 2–3 年主流，调参是否公正？
3. 有无消融、敏感性、统计显著性（方差/误差棒）？
4. 有无失效案例与局限性，而不是只报最高分？
5. 正文和表格中的实验数字，能否在代码、配置、日志或结果文件中对上？
6. 论文所述模型结构（模块组成、层数、维度、骨干、损失组成、参数量）与代码实现是否一致？
7. 论文所报超参数（优化器、学习率、batch、epoch、权重衰减、种子、调度）与配置文件或训练脚本是否一致？
8. 实验设计（数据集版本与划分、预处理、基线实现与版本、指标定义、评测协议、重复次数）与数据/评测脚本是否一致？

指标必须服务任务本质；分类任务只报 Acc、检测任务只报 mAP 却不分析错误类型，应降级可信度。

## 代码对账（深审必填）

实验充分度不以实验报告或修订说明为终证。**实验数字、模型结构、超参数、实验设计**四类主张都要落到脚本、配置、日志或结果表：数字全对但结构是两套实现、超参表与配置不符、划分比例对不上，结论同样不可信。先找代码根目录：用户给出的路径、工作区旁的工程目录、`results/`、`configs/`、模型定义与训练脚本。找不到就写明找过哪里。

每个维度至少一行；不适用时在 `aspects_skipped` 写明理由（如「理论稿无训练配置」），不得静默跳过：

| `aspect` | 核对什么 | 典型证据 |
| --- | --- | --- |
| `number` | 主结果、消融、正文引用的增益等定量数字 | 结果表、日志、csv |
| `architecture` | 模块组成、层数、维度、骨干、损失组成、参数量 | 模型定义文件、结构配置 |
| `hyperparameter` | 优化器、学习率、batch、epoch、权重衰减、种子、调度 | `configs/`、argparse 默认值、训练脚本 |
| `design` | 数据集版本与划分、预处理、基线实现与版本、指标定义、评测协议 | 数据脚本、split 文件、评测脚本 |

`code_status` 只能取下表之一。

| 值 | 何时使用 |
| --- | --- |
| `pending` | 尚未对账。`consolidator.status=done` 时 `doctor` 失败 |
| `missing` | 找不到可核对的代码或结果文件 |
| `partial` | 只核对了部分主张，其余行标 `unverifiable` |
| `checked` | 四个维度均已对账或写明跳过理由，且没有 `unverifiable` |

`missing` 且论文含定量结果时，写一条 Major，并用 `code_note` 记录检索范围。纯理论稿设 `"quantitative_claims": false`（仅豁免 `number` 维度）。对不上记 Major 并写入 `findings`：结构或实验设计对不上一律 Major；超参不一致默认 Major（破坏可复现性），仅打印/记录性偏差可 Minor。同一数字仅是文件名或指标别名不同，记 Minor。作者修订说明不能代替打开结果文件。

每行字段：`claim`（主张）、`aspect`（维度）、`paper_ref`（论文定位：章节/表/图/公式）、`paper_quote`（原文摘引，`mismatch` 必填，供 Major 锚定）、`paper_value`（论文取值或描述）、`code_ref`（文件或结果位置）、`code_value`（代码取值）、`verdict`。

```json
{
  "status": "done",
  "agent": "C",
  "quantitative_claims": true,
  "code_status": "checked",
  "code_roots": ["results/main", "configs", "src/models"],
  "code_note": "",
  "aspects_skipped": {"design": "数据划分脚本未随仓库提供，划分仅在 3.2 文字说明"},
  "code_correspondence": [
    {
      "claim": "表5.1 主模型 macro-F1",
      "aspect": "number",
      "paper_ref": "5.3 表5.1",
      "paper_quote": "macro-F1 0.812±0.01",
      "paper_value": "0.812±0.01",
      "code_ref": "results/main/foldmean.csv",
      "code_value": "0.812",
      "verdict": "match"
    },
    {
      "claim": "融合模块为 4 头注意力、维度 256、2 层堆叠",
      "aspect": "architecture",
      "paper_ref": "4.2 图4.1",
      "paper_quote": "多头注意力采用 4 个头，嵌入维度 256，堆叠 2 层",
      "paper_value": "4 头 / d=256 / 2 层",
      "code_ref": "src/models/fusion.py:56、configs/main.yaml",
      "code_value": "nhead=4 / d_model=256 / num_layers=2",
      "verdict": "match"
    },
    {
      "claim": "训练学习率 1e-3、批大小 128",
      "aspect": "hyperparameter",
      "paper_ref": "5.2 表5.3",
      "paper_quote": "初始学习率 1e-3，批大小 128",
      "paper_value": "lr=1e-3 / batch=128",
      "code_ref": "configs/main.yaml",
      "code_value": "lr=3e-4 / batch=64",
      "verdict": "mismatch"
    }
  ],
  "findings": []
}
```

`verdict` 只能是 `match`、`mismatch`、`unverifiable`。`mismatch` 必须给出 `code_value` 与 `paper_quote`。历史 run 若没有 `code_status` 字段，`doctor` 不追溯。
