# 发布到 GitHub 计划（待审阅，未执行）

**状态：已执行。** 仓库 https://github.com/qyyyy09315/thesis-review-pipeline

**Goal:** 把当前审稿工作区整理成公开 Git 仓库并推送，README 写明借鉴的 GitHub 项目与论文链接。

**Repo:** `thesis-review-pipeline`  
**Remote:** `git@github.com:qyyyy09315/thesis-review-pipeline.git`  
**Visibility:** public  
**Default branch:** `main`  
**License:** MIT

---

## 1. 工作汇总（将写入 README 顶部）

本仓库是高水平**本科毕业设计**审稿流水线，不是 SCI 深审器，也不是改稿器。

已落地：

- 三阶段：Stage 1 机械预检（符号 / 过强断言 / 结构缺口）→ Agent A/B/C 分审骨架 → Stage 3 四段式报告
- CLI：`scripts/thesis_review.py`（ingest / lint / init-run / render / 可选 paper-audit）
- 项目技能 `thesis-review`、Python 3.12 `.venv`、12 项 pytest
- 样例 run：定级「退修」，含五维评分卡、问题–证据表、Markdown + HTML

硬约束：只审不改论文源文件；默认离线。

---

## 2. 仓库名

推荐 **`ug-thesis-review`**（已确认 `qyyyy09315` 下未占用）。

| 候选 | 理由 |
| --- | --- |
| **ug-thesis-review（推荐）** | undergraduate thesis；短、可搜、不和 `paper-audit` 撞名 |
| `thesis-review-pipeline` | 强调流水线，略长 |
| `biyesheji-reviewer` | 中文检索友好，GitHub 英文生态里偏口语 |

中文显示名：高水平本科毕业设计审稿工作流。

---

## 3. README 将增加的「借鉴」段落（批准后写入，不现在改）

明确写出链接，不用「参考了相关工作」这种空话：

- 借鉴 [AliManjotho/open-reviewer](https://github.com/AliManjotho/open-reviewer) 的评分卡、问题–证据表、HTML 双输出。
- 借鉴 [FanBroWell/AI-paper-reviewer](https://github.com/FanBroWell/AI-paper-reviewer) 的过强 claim / 红旗分级（映射为 linter 的 OC\* 与 Major/Minor）。
- 流程形状参考 [Ahren09/AgentReview](https://github.com/Ahren09/AgentReview) 的分角色再聚合，以及 [allenai/marg-reviewer](https://github.com/allenai/marg-reviewer) 的章节专精 Agent。
- PDF→Markdown 必要性对照 [maxidl/openreviewer](https://github.com/maxidl/openreviewer)。
- 论文：[MARG](https://arxiv.org/abs/2401.04259)、[AgentReview](https://arxiv.org/abs/2406.12708)、[OpenReviewer](https://arxiv.org/abs/2412.11948)。

同时写清：**不 fork 上述仓库**；它们面向顶会仿真或提示词箱，没有中文毕设四段合同。

---

## 4. 纳入 / 排除

**提交：**

- `scripts/` `templates/` `tests/` `docs/` `papers/sample_thesis.md` `requirements.txt` `README.md` `AGENTS.md` `LICENSE`
- `.agents/skills/thesis-review/` `.python-version` `.gitignore`
- 样例产物（gitignore 开例外）：`runs/20260917-112554-sample_thesis/`

**不提交：**

- `.venv/` `.pytest_cache/` `__pycache__/`
- `.zcode/`（与 `.agents` 技能重复）
- 系统 Python 用户库；真实学生论文（`papers/` 只留样例）

提交身份沿用本机 git 全局配置（不在公开文档中重复邮箱）。

---

## 5. 批准后执行步骤（现在不跑）

1. 更新 README：中文简介、快速开始（`.venv`）、借鉴项目链接表、样例 run 路径。
2. 补 `LICENSE`（MIT）。
3. `.gitignore` 增加 `!runs/20260917-112554-sample_thesis/` 及其文件例外。
4. `git init -b main` → `git add` → 一次初始 commit。
5. `gh repo create ug-thesis-review --public --source=. --remote=origin --push --description "Undergraduate thesis review pipeline: linter, multi-agent prompts, four-part reports."`
6. 回写 `docs/worklog.md` 仓库 URL。

若你改名或改 private，只替换第 5 步对应参数。

---

## 6. 需要你拍板的点

- 仓库名是否用 `ug-thesis-review`
- public 还是 private
- 是否把样例 `runs/20260917-112554-sample_thesis` 一并公开
