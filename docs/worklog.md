# 审稿工作日志

本文件由 CLI 自动追加，并允许人工补记会话级决策。最新 CLI 记录在最下方。

---

## 2026-09-17 会话：从空工作区落地审稿流水线

### 决策

- 路径判定为架构型：空仓库 + 用户给定三阶段 Agent 架构 + 四段式报告合同。
- 不重复造 SCI 深审轮子：`.tex/.typ/.pdf` 可选封装已有 `paper-audit`；本科毕设主路径自建 ingest → linter → A/B/C → 四段式报告。
- 默认离线，禁止未授权文献外搜。
- 只审不改论文源文件。

### 技能安装

| 技能 | 位置 | 说明 |
| --- | --- | --- |
| `thesis-review`（新建） | 工作区 `.agents/skills/`、`.zcode/skills/`；全局 `~/.agents/skills/`、`~/.zcode/skills/` | 本科毕设审稿主技能，中文 description |
| `docx-to-markdown` | `npx skills add duc01226/easyplatform@docx-to-markdown -g -y` | PromptScript 全局安装失败可忽略；ZCode/agents 已 symlink |
| `paper-audit` | 已有 | 可选 quick-audit |
| `latex-thesis-zh` | 已有 | 中文 LaTeX 格式/国标 |

`docx-to-markdown` 的 `description` 已改为中文触发语。

检索过但未安装：`evoscientist/evoskills@paper-review`（480 installs，与现有 paper-audit 重叠且不针对中文毕设合同）。

### Python 依赖

已安装并核验：`pymupdf` 1.28.2、`pymupdf4llm` 1.28.2、`python-docx` 1.2.0、`mammoth`、`markdownify`、`Jinja2` 3.1.6、`pytest`。用户级 Scripts 不在 PATH，测试统一用 `python -m pytest`。锁定文件：`requirements.txt`。

### 验证

- `python -m pytest tests -q` → 10 passed
- 烟雾：`python scripts/thesis_review.py init-run papers/sample_thesis.md --title "基于改进注意力机制的图像分类方法研究" --field "计算机科学与技术"`
- 产物：[review_report.md](runs/20260917-112554-sample_thesis/review_report.md)
- 样例定级：**退修**；未定义符号 3、过强断言 6、结构缺口 6；四段标题齐全。

### 使用方式

把论文放入 `papers/`，然后：

```bash
.venv/Scripts/python.exe scripts/thesis_review.py init-run papers/<文件> --title "题目" --field "专业"
.venv/Scripts/python.exe scripts/thesis_review.py render runs/<id>
```

---

## 2026-09-17 11:25:54

init-run `sample_thesis.md` → `20260917-112554-sample_thesis`，定级 退修，报告 `review_report.md`

- ingest: `ingest/sample_thesis.md`
- linter: `runs/20260917-112554-sample_thesis/stage1/linter.json`

## 2026-09-17 11:28:02

render `20260917-112554-sample_thesis` → `runs/20260917-112554-sample_thesis/review_report.md`

修复：空的 `consolidator.json.roadmap` 不再覆盖默认二稿路线图。

## 2026-09-17 项目虚拟环境

选定 **CPython 3.12.13**（uv 管理的官方构建），在仓库根目录创建 `.venv`，避免继续往系统 Python 3.14 堆库。

```bash
uv venv .venv --python 3.12
uv pip install -r requirements.txt --python .venv/Scripts/python.exe
.venv/Scripts/python.exe -m pytest tests -q   # 10 passed
```

解释器：`.venv/Scripts/python.exe`  
已写入 `.python-version`、README、AGENTS.md、thesis-review 技能。`.gitignore` 已忽略 `.venv/`。

## 2026-09-17 GitHub 对照与增量

检索并阅读：open-reviewer、AI-paper-reviewer、AgentReview、MARG、OpenReviewer。结论：无现成中文毕设审稿流水线可直接 fork。已吸收评分卡、问题–证据表、HTML 报告到 `scripts/scorecard.py` 与 render；清单见 `docs/references.md`。
## 2026-09-17 11:44:11

render `20260917-112554-sample_thesis` → `runs/20260917-112554-sample_thesis/review_report.md`

## 2026-09-17 GitHub 发布

仓库：https://github.com/qyyyy09315/thesis-review-pipeline （public）。样例 run 公开；`papers/` 与后续 `runs/` 默认忽略，避免真实论文入库。

## 2026-09-17 12:34:35

render `20260917-112554-sample_thesis` → `runs/20260917-112554-sample_thesis/review_report.md`

