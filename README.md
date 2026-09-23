<div align="center">

# thesis-review-pipeline 毕设行止

### *“纸上得来终觉浅”*

<br>

[![Python 3.12](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-2ea44f)](LICENSE)
[![Default: offline](https://img.shields.io/badge/default-offline-0f766e)](AGENTS.md)
[![Review only](https://img.shields.io/badge/policy-review--only-6d28d9)](AGENTS.md)

中文工科、理科本科毕业设计初稿的审稿流水线，产出四段式报告、定级和二稿路线图。不改写正文，默认离线。

</div>

---

## 工作流原理

<p align="center"><img src="docs/assets/workflow.svg" alt="审稿流水线：papers 原稿 → ingest 归一 → Stage 1 预检 → A/B/C 分审 → consolidator → 四段式报告" width="860"/></p>

稿件从 `papers/` 归一成 Markdown，先过一遍机械预检，查未定义符号、过强断言和结构缺口。
预检之后分三路审查：A 管动机与文献边界，B 管方法严密性，C 管实验充分度和代码–论文对账。
consolidator 汇总三路意见，生成四段式报告和二稿路线图。每一步都记进工作日志。

定级分优秀、良好、及格、退修四档。虚构样例，定级退修：[review_report.md](runs/20260917-112554-sample_thesis/review_report.md)

## 快速开始

待审稿放进 `papers/`，真实稿件不要入库：

```bash
pip install -r requirements.txt

python scripts/thesis_review.py init-run papers/你的论文.md --title "题目" --field "专业"
python scripts/thesis_review.py render runs/<id>
```

跑完 `init-run`，`runs/<时间>-<稿名>/` 里就有预检结果、分审骨架和初稿报告。

<details>
<summary><b>全部子命令</b></summary>

| 子命令 | 作用 |
| --- | --- |
| `ingest <file>` | 归一为 UTF-8 Markdown；`--versioned` 加时间戳后缀防覆盖 |
| `lint <file>` | Stage 1 预检；`--json` 输出结构化结果 |
| `init-run <file>` | ingest + lint + 分审骨架 + 初稿报告（定级「待深审」） |
| `render <run_dir>` | 按 `agents/*.json` 重渲染四段式报告 |
| `ledger add/close/list` | 跨轮问题台账，报告自动附「跨轮遗留」 |
| `sanitize` | 清洗日志中的本机绝对路径；**提交前必跑** |
| `doctor` | 体检：日志对账、路径泄漏、consolidator 状态、代码–论文对账 |
| `audit <file>` | 可选封装 `paper-audit`（仅 `.tex` / `.typ` / `.pdf`，未安装则退出码 2） |

</details>

## 规范索引

给 Agent 看的合同和约束以这些文档为准：

| 文档 | 内容 |
| --- | --- |
| [AGENTS.md](AGENTS.md) | 硬约束与执行入口 |
| [thesis-review 技能](.agents/skills/thesis-review/SKILL.md) | 审稿工作流细则与执行清单 |
| [templates/agents/](templates/agents) | A / B / C / consolidator 分审合同 |
| [templates/review_report.md.j2](templates/review_report.md.j2) | 报告合同的四级标题模板 |
| [docs/worklog.md](docs/worklog.md) | 工作日志 |
| [docs/references.md](docs/references.md) | 外部项目取舍 |

<details>
<summary><b>外部参考</b>（不 fork，只吸收机制）</summary>

| 项目 | 吸收了什么 |
| --- | --- |
| [AliManjotho/open-reviewer](https://github.com/AliManjotho/open-reviewer) | 评分卡、问题–证据表、Markdown + HTML 双输出 |
| [FanBroWell/AI-paper-reviewer](https://github.com/FanBroWell/AI-paper-reviewer) | 过强 claim / 红旗分级 → linter 的 OC* 与 Major / Minor |
| [Ahren09/AgentReview](https://github.com/Ahren09/AgentReview) | 分角色再聚合的流程形状（A / B / C + consolidator） |
| [allenai/marg-reviewer](https://github.com/allenai/marg-reviewer) | 按章节专精的 Agent，替代单篇超长提示词 |
| [maxidl/openreviewer](https://github.com/maxidl/openreviewer) | PDF→Markdown 作为审稿输入 |

论文：[MARG](https://arxiv.org/abs/2401.04259) · [AgentReview](https://arxiv.org/abs/2406.12708) · [OpenReviewer](https://arxiv.org/abs/2412.11948)。
改写类仓库（和「只审不改」相反）以及同名的代码评审 Agent 都不吸收。

</details>

---

<div align="center">

<sub>公开仓库只跟踪虚构样例 <a href="papers/sample_thesis.md">sample_thesis.md</a> 与对应样例 run；真实毕业设计材料一律不入库 · <a href="LICENSE">MIT</a></sub>

</div>
