---
name: thesis-review
description: 高水平本科毕业设计/学位论文初稿审稿与挑刺。用于校级优秀、答辩评阅、四段式审稿报告、消融缺失诊断、符号预检、实验数字与代码或日志对不上、模型结构或超参与论文不符、代码-论文四维对账、二稿修改路线图；用户说审稿、评阅、毕业设计评审时使用。
---

# 本科毕业设计审稿工作流

在当前工作区评审中文工科/理科本科毕业设计初稿。只审不改论文源文件。

**REQUIRED SUB-SKILL:** 英文 SCI 深审用 `paper-audit`；中文 LaTeX 格式/国标用 `latex-thesis-zh`。

## 何时使用

- 用户要把工作区建成审稿流水线，或对 `papers/` 中的稿件做优秀毕设标准评审
- 需要四段式报告：总体评价 / Major / Minor / 二稿路线图
- 输入为 `.md` `.docx` `.pdf` `.tex` `.typ`

不要用于：直接改写正文、生成投稿信、纯文献综述写作。

## 流水线

```
ingest → Stage1 linter → Agent A/B/C 分审 → consolidator → render 四段式报告 → worklog
```

入口（在工作区根目录，使用项目 `.venv` / CPython 3.12）：

```bash
.venv/Scripts/python.exe scripts/thesis_review.py init-run <论文路径> --title "题目" --field "专业"
.venv/Scripts/python.exe scripts/thesis_review.py render runs/<id>
```

`init-run` 已完成 Stage 1，并生成带预检证据的初稿报告（Markdown + HTML、五维评分卡、问题–证据表）。深审时按下面顺序填 JSON，再 `render`。外部对照见 `docs/references.md`。

## 执行清单

1. 确认论文路径；复制或指向 `papers/`。默认离线，未经用户明确要求不要外搜文献。重复审稿的 docx 用 `ingest --versioned` 避免同名覆盖。
2. 运行 `init-run`。阅读 `runs/<id>/stage1/linter.md`。`init-run` 定级记为「待深审」，`metadata.grade_suggested` 只是机械预检建议。
3. 先读 `ledger list`：上一轮未闭环项必须逐条核销或继续追踪。
4. 按 `templates/agents/` 填写：
   - A 动机与文献边界 → `agents/agent_a_motivation.json`
   - B 方法严密性 → `agents/agent_b_methodology.json`
   - C 实验充分度 → `agents/agent_c_experiments.json`。四类主张（数字/结构/超参/实验设计）先做代码对账，再写 findings
   - 聚合 → `agents/consolidator.json`
5. 深审结束把 `consolidator.status` 改为 `done`，并把 Stage 1 每条结构缺口写入 `linter_triage`（accept/reject + 依据）；`done` 后 `majors`/`minors` 空列表 = 确认无，render 不再机械兜底。
6. 新问题 `ledger add`，已闭环 `ledger close`，再 `render`。核对报告含且仅含 spec 规定的四级标题。
7. 向 `docs/worklog.md` 追加本轮结论（CLI 已自动写一条；深审结束后再补一条人工摘要）。提交 git 前跑 `sanitize` + `doctor`。

## 代码–论文对账（数字 / 结构 / 超参 / 实验设计）

Agent C 在写实验意见之前填写 `code_correspondence`。论文表格、实验报告和作者修订说明都不是终证，打开脚本、配置、日志或结果文件核对。数字全对但结构是两套实现、超参表与配置不符、划分比例对不上，结论同样不可信，四类主张都要对账：

1. `number`：主结果、消融，以及正文里的增益等定量数字。
2. `architecture`：模块组成、层数、维度、骨干、损失组成、参数量 ↔ 模型定义文件、结构配置。
3. `hyperparameter`：优化器、学习率、batch、epoch、权重衰减、种子、调度 ↔ `configs/`、argparse 默认值、训练脚本。
4. `design`：数据集版本与划分、预处理、基线实现与版本、指标定义、评测协议 ↔ 数据脚本、split 文件、评测脚本。

执行步骤：

1. 记录 `code_roots`。用户未给路径时，在工作区及相邻工程目录中查找；仍没有则 `code_status=missing`，`code_note` 写明找过的位置。
2. 每条主张占一行。字段为 `claim`、`aspect`、`paper_ref`（章节/表/图/公式定位）、`paper_quote`（原文摘引，`mismatch` 必填）、`paper_value`、`code_ref`、`code_value`、`verdict`（`match` / `mismatch` / `unverifiable`）。
3. 四个维度各须有对账行；不适用时在 `aspects_skipped` 写明理由，不得静默跳过。纯理论稿设 `quantitative_claims: false`（仅豁免 `number`）。
4. `mismatch` 写成 Major（结构/设计不一致一律 Major；超参仅记录性偏差可 Minor），写出论文与代码两边的取值。`missing` 或 `partial` 时，未核对的主张不得写成已复核；论文有定量结果则 Major 写明无法对账。
5. `consolidator.status=done` 前，`code_status` 必须是 `missing`、`partial` 或 `checked`。`doctor` 检查该字段与四维覆盖；没有该字段的历史 run 不追溯。

合同见 `templates/agents/agent_c_experiments.md`。

## 报告合同

标题必须原样出现：

- `### 一、 总体评价与学术定位（Executive Summary）`
- `### 二、 实质性修改意见（Major Comments - 关乎学术严谨性与论证逻辑）`
- `### 三、 规范性与细节性修改意见（Minor Comments - 关乎格式、符号与表达）`
- `### 四、 二稿修改路线图与落地行动计划（Actionable Revision Roadmap）`

Major 每条：定位 + 具体问题 + 理论/学术依据 + 建议改进措施。  
定级：优秀 / 良好 / 及格 / 退修。机械预检不得单独给优秀。

## 硬规则

| 借口 | 现实 |
| --- | --- |
| 先帮作者改一改更高效 | 审稿证据必须与编辑分离 |
| 没有摘引也能写 Major | 无定位的意见无法复审 |
| 补几篇“经典文献”撑场面 | 禁止虚构引用 |
| 预检通过就是优秀 | 预检只排除机械问题 |
| 实验章节写清楚了，不必再翻代码 | 数字、结构、超参、设计都要和脚本、配置、日志或结果文件一致 |
| 作者修订说明已经对过 CSV | 修订说明不是证据，打开结果文件 |
| 仓库里没有代码，就当实验充分 | `code_status=missing`，定量主张记 Major |
| 只核对主表一行 | 消融、正文增益、结构与超参都要入表；没覆盖的标 `unverifiable`/`partial` |
| 论文结构描述和代码没关系，看看实验就行 | 结构/超参/设计对不上结论就不可复现，逐维对账 |

`.tex/.typ/.pdf` 需要 `paper-audit` 机械层时：

```bash
.venv/Scripts/python.exe scripts/thesis_review.py audit <file> --mode quick-audit --lang zh
```
