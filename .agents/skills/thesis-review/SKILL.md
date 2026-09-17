---
name: thesis-review
description: 高水平本科毕业设计/学位论文初稿审稿与挑刺。用于校级优秀、答辩评阅、四段式审稿报告、消融缺失诊断、符号预检、二稿修改路线图；用户说审稿、评阅、毕业设计评审时使用。
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

1. 确认论文路径；复制或指向 `papers/`。默认离线，未经用户明确要求不要外搜文献。
2. 运行 `init-run`。阅读 `runs/<id>/stage1/linter.md`。
3. 按 `templates/agents/` 填写：
   - A 动机与文献边界 → `agents/agent_a_motivation.json`
   - B 方法严密性 → `agents/agent_b_methodology.json`
   - C 实验充分度 → `agents/agent_c_experiments.json`
   - 聚合 → `agents/consolidator.json`
4. `render`。核对报告含且仅含 spec 规定的四级标题。
5. 向 `docs/worklog.md` 追加本轮结论（CLI 已自动写一条；深审结束后再补一条人工摘要）。

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

`.tex/.typ/.pdf` 需要 `paper-audit` 机械层时：

```bash
.venv/Scripts/python.exe scripts/thesis_review.py audit <file> --mode quick-audit --lang zh
```
