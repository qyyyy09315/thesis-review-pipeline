# Agent C：实证充分度与数据可信度审查

填写 `agent_c_experiments.json`。重点实验与分析章。

## 必查

1. 数据集规模、划分、预处理是否可复现？
2. 基线是否代表近 2–3 年主流，调参是否公正？
3. 有无消融、敏感性、统计显著性（方差/误差棒）？
4. 有无失效案例与局限性，而不是只报最高分？
5. 正文和表格中的实验数字，能否在代码、配置、日志或结果文件中对上？

指标必须服务任务本质；分类任务只报 Acc、检测任务只报 mAP 却不分析错误类型，应降级可信度。

## 代码对账（深审必填）

实验充分度不以实验报告或修订说明为终证。主结果、消融，以及正文引用的增益，都要落到脚本、配置、日志或结果表。先找代码根目录：用户给出的路径、工作区旁的工程目录、`results/`、`configs/`、训练脚本。找不到就写明找过哪里。

`code_status` 只能取下表之一。

| 值 | 何时使用 |
| --- | --- |
| `pending` | 尚未对账。`consolidator.status=done` 时 `doctor` 失败 |
| `missing` | 定量实验没有可核对的代码或结果文件 |
| `partial` | 只核对了部分主张，其余行标 `unverifiable` |
| `checked` | 本轮所依赖的定量主张各有一行，且没有 `unverifiable` |

`missing` 且论文含定量结果时，写一条 Major，并用 `code_note` 记录检索范围。纯理论稿设 `"quantitative_claims": false`。数字对不上记 Major，并写入 `findings`。同一数字仅是文件名或指标别名不同，记 Minor。作者修订说明不能代替打开结果文件。

```json
{
  "status": "done",
  "agent": "C",
  "quantitative_claims": true,
  "code_status": "checked",
  "code_roots": ["results/main"],
  "code_note": "",
  "code_correspondence": [
    {
      "claim": "表5.1 主模型 macro-F1",
      "paper_value": "0.812±0.01",
      "code_ref": "results/main/foldmean.csv",
      "code_value": "0.812",
      "verdict": "match"
    }
  ],
  "findings": []
}
```

`verdict` 只能是 `match`、`mismatch`、`unverifiable`。`mismatch` 必须给出 `code_value`。历史 run 若没有 `code_status` 字段，`doctor` 不追溯。
