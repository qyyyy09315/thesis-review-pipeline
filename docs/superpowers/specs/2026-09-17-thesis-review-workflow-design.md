# 高水平本科毕业设计审稿工作流 — 设计规范

日期：2026-09-17  
范围：当前空工作区从零落地可复用审稿流水线，不改写论文正文。

## 问题

本科毕设初稿审稿需要同时覆盖：格式/符号预检、动机与文献边界、方法严密性、实验充分度。单次超长提示词会漏审公式与图表，也无法留下可复核的证据链。本工作区要把用户给出的三阶段架构固化为「脚本可重复 + Agent 可分审 + 四段式报告」的本地工作流。

## 目标用户与成功标准

- 使用者：评阅人或协助评阅的 Agent，处理中文工科/理科本科毕业设计初稿。
- 输入：`papers/` 下的 `.md` / `.tex` / `.typ` / `.pdf` / `.docx`。
- 输出：每次运行一个独立 `runs/<id>/`，内含 Stage 1 机械预检、分审提示词、四段式审稿报告、工作日志。
- 成功标准：
  1. 对样例文稿，linter 能稳定检出未定义符号与悬空断言。
  2. `init-run` 一次命令即可完成 ingest + lint + 工作区骨架。
  3. 最终报告严格包含：总体评价、Major、Minor、二稿路线图。
  4. 每次命令向工作日志追加一条可追溯记录。

## 非目标

- 不自动改写论文源文件。
- 不默认把标题/摘要发到第三方文献 API（除非用户明确要求 `--online`）。
- 不替代 `paper-audit` 的 SCI 深审；对 `.tex/.typ/.pdf` 只做可选封装。

## 架构

```
papers/<manuscript>
        │
        ▼
  ingest.py  →  ingest/<slug>.md
        │
        ▼
  linter.py  →  stage1_linter.json / .md
        │
        ├── (可选) paper-audit quick-audit   # 仅 tex/typ/pdf
        │
        ▼
  agents/A,B,C 提示词骨架  →  LLM 分审填写 JSON
        │
        ▼
  render.py  →  review_report.md（四段式）
        │
        ▼
  worklog 追加
```

三阶段与用户方案对齐：

| 阶段 | 执行者 | 产物 |
| --- | --- | --- |
| Stage 1 Pre-flight Linter | 确定性 Python | 符号表、悬空断言、结构缺口 |
| Stage 2 Deep Review | Agent A/B/C（提示词约束） | `agents/*.json` + markdown |
| Stage 3 Consolidator | 脚本渲染 + Agent 聚合 | 四段式 `review_report.md` |

## 组件边界

- `scripts/ingest.py`：格式归一到 Markdown，不审内容。
- `scripts/linter.py`：只做可复现规则，禁止主观评分当终审。
- `scripts/workspace.py`：创建 run 目录与元数据。
- `scripts/render.py`：把 JSON 填进四段式模板。
- `scripts/thesis_review.py`：唯一 CLI。
- `scripts/worklog.py`：追加 `docs/worklog.md` 与 `runs/<id>/worklog.md`。
- `.agents/skills/thesis-review/SKILL.md`：告诉 Agent 何时调用、如何分审。

## 报告合同

`review_report.md` 必须按此四级标题输出，不得增删：

1. `### 一、 总体评价与学术定位（Executive Summary）`
2. `### 二、 实质性修改意见（Major Comments - 关乎学术严谨性与论证逻辑）`
3. `### 三、 规范性与细节性修改意见（Minor Comments - 关乎格式、符号与表达）`
4. `### 四、 二稿修改路线图与落地行动计划（Actionable Revision Roadmap）`

每条 Major 必须含：定位 + 具体问题 + 理论/学术依据 + 建议改进措施。

定级枚举：`优秀` / `良好` / `及格` / `退修`。机械预检不得单独给出「优秀」。

## 依赖

已安装并核验：

- `pymupdf` 1.28.2、`pymupdf4llm` 1.28.2（PDF）
- `python-docx` 1.2.0、`mammoth`、`markdownify`（DOCX）
- 全局技能：`paper-audit`、`latex-thesis-zh`、`docx-to-markdown`

本仓库 `requirements.txt` 锁定上述包，便于换机复现。
