# Thesis Review Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在空的审稿工作区落地「ingest → Stage1 linter → 分审骨架 → 四段式报告 → 工作日志」可运行流水线。

**Architecture:** 确定性 Python 负责解析与预检；Agent 技能负责 A/B/C 分审与聚合；每次审稿写入独立 `runs/<id>/`，不修改论文源文件。

**Tech Stack:** Python 3.14、PyMuPDF / pymupdf4llm、mammoth、markdownify、Jinja2、pytest；复用已安装的 `paper-audit` 与 `docx-to-markdown`。

**Spec:** `docs/superpowers/specs/2026-09-17-thesis-review-workflow-design.md`

## Global Constraints

- 不改写论文正文；审稿与编辑必须分离。
- 默认不启用 `--online` / 文献外搜。
- 报告四级标题必须与 spec 完全一致。
- 技能 `description` 使用中文触发语。
- 工作日志每次 CLI 运行追加，禁止事后补写空话。

---

### Task 1: 仓库骨架与依赖锁定

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `papers/.gitkeep`
- Create: `runs/.gitkeep`
- Create: `ingest/.gitkeep`
- Create: `logs/.gitkeep`

- [x] **Step 1: 锁定 Python 依赖**
- [x] **Step 2: 忽略缓存与运行产物中的大文件，保留目录占位**

### Task 2: Stage 1 Linter（TDD）

**Files:**
- Create: `scripts/linter.py`
- Create: `tests/test_linter.py`
- Create: `tests/fixtures/sample_thesis.md`

**Interfaces:**
- Consumes: Markdown 文本
- Produces: `LintResult.to_dict()`，含 `symbols` / `overclaims` / `structure_gaps`

- [x] **Step 1: 写失败测试（未定义符号、悬空断言、缺消融）**
- [x] **Step 2: 实现最小 linter 使测试通过**

### Task 3: Ingest + Workspace + CLI

**Files:**
- Create: `scripts/ingest.py`
- Create: `scripts/workspace.py`
- Create: `scripts/worklog.py`
- Create: `scripts/render.py`
- Create: `scripts/thesis_review.py`
- Create: `templates/review_report.md.j2`
- Create: `tests/test_ingest.py`
- Create: `tests/test_render.py`

- [x] **Step 1: Markdown/DOCX/PDF ingest**
- [x] **Step 2: `init-run` 生成 run 目录、linter 产物、Agent 骨架**
- [x] **Step 3: `render` 输出四段式报告**
- [x] **Step 4: 每条命令写 worklog**

### Task 4: 技能、分审提示词与全局安装

**Files:**
- Create: `.agents/skills/thesis-review/SKILL.md`
- Create: `templates/agents/stage1_linter.md`
- Create: `templates/agents/agent_a_motivation.md`
- Create: `templates/agents/agent_b_methodology.md`
- Create: `templates/agents/agent_c_experiments.md`
- Create: `templates/agents/consolidator.md`

- [x] **Step 1: 写中文 description 的项目技能**
- [x] **Step 2: 同步到 `~/.agents/skills/thesis-review` 与 `~/.zcode/skills/thesis-review`**
- [x] **Step 3: 将 `docx-to-markdown` 的 description 改为中文**

### Task 5: 烟雾验证与工作日志

- [x] **Step 1: `pytest tests -q`**
- [x] **Step 2: `python scripts/thesis_review.py init-run tests/fixtures/sample_thesis.md`**
- [x] **Step 3: 将安装、测试、烟雾结果写入 `docs/worklog.md`**
