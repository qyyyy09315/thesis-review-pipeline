# thesis-review-pipeline

高水平**本科毕业设计**审稿流水线：机械预检 → A/B/C 分审骨架 → 四段式报告。面向校级优秀 / 具备发表潜力的工科、理科初稿。

只审不改论文源文件。默认离线，不把稿件发到第三方文献 API。

## 它做什么

1. **Stage 1** 确定性 linter：未定义符号、过强断言、结构缺口（综述 / 形式化 / 消融 / 基线等）。「未做消融」不会被当成已经做了。
2. **Stage 2** Agent A/B/C 提示词：动机与文献、方法严密性、实验充分度。
3. **Stage 3** 聚合成四段式报告：总体评价 / Major / Minor / 二稿路线图，附五维评分卡与问题–证据表。

样例 run（虚构稿，定级退修）：[`runs/20260917-112554-sample_thesis/review_report.md`](runs/20260917-112554-sample_thesis/review_report.md)

## 环境

Python **3.12** 虚拟环境（`.venv`）。不要往系统 Python 里堆库。

```bash
uv venv .venv --python 3.12
uv pip install -r requirements.txt --python .venv/Scripts/python.exe
source .venv/Scripts/activate          # Git Bash
# .venv\Scripts\activate               # cmd / PowerShell
```

未激活时用：

```bash
.venv/Scripts/python.exe scripts/thesis_review.py init-run papers/sample_thesis.md --title "题目" --field "计算机科学与技术"
```

## 快速开始

把**待审稿**放进 `papers/`（该目录除样例外默认不入库），然后：

```bash
.venv/Scripts/python.exe scripts/thesis_review.py init-run papers/你的论文.md --title "题目" --field "专业"
.venv/Scripts/python.exe scripts/thesis_review.py render runs/<id>
```

| 路径 | 含义 |
| --- | --- |
| `paper.md` | 归一后的审稿用文本 |
| `stage1/linter.md` | 符号、过强断言、结构缺口 |
| `agents/*.json` | 分审填写处 |
| `review_report.md` | 四段式报告 |
| `review_report.html` | 同内容 HTML |

`.tex` / `.typ` / `.pdf` 可额外调用已安装的 `paper-audit`：

```bash
.venv/Scripts/python.exe scripts/thesis_review.py audit papers/xxx.pdf --mode quick-audit --lang zh
```

## 测试

```bash
.venv/Scripts/python.exe -m pytest tests -q
```

## 隐私

公开仓库**只**跟踪虚构样例 `papers/sample_thesis.md` 和对应样例 run。真实毕业设计、学号、姓名、学校内部材料不要 `git add`。后续审稿 run 被 `runs/*` 忽略。日志与 `metadata.json` 只写相对路径。

## 借鉴的项目与论文

本仓库不 fork 下列项目：它们面向顶会仿真、专用审稿模型或提示词箱，没有中文本科毕设四段合同。吸收的是机制。

| 项目 | 借鉴了什么 |
| --- | --- |
| [AliManjotho/open-reviewer](https://github.com/AliManjotho/open-reviewer) | 评分卡、问题–证据表、Markdown + HTML 双输出 |
| [FanBroWell/AI-paper-reviewer](https://github.com/FanBroWell/AI-paper-reviewer) | 过强 claim / 红旗分级，映射为 linter 的 OC\* 与 Major/Minor |
| [Ahren09/AgentReview](https://github.com/Ahren09/AgentReview) | 分角色再聚合的流程形状（对应 A/B/C + consolidator） |
| [allenai/marg-reviewer](https://github.com/allenai/marg-reviewer) | 章节专精 Agent，而不是一篇超长提示词 |
| [maxidl/openreviewer](https://github.com/maxidl/openreviewer) | PDF→Markdown 作为审稿输入的必要性 |

论文：[MARG (arXiv:2401.04259)](https://arxiv.org/abs/2401.04259)、[AgentReview (arXiv:2406.12708)](https://arxiv.org/abs/2406.12708)、[OpenReviewer (arXiv:2412.11948)](https://arxiv.org/abs/2412.11948)。更完整的取舍见 [`docs/references.md`](docs/references.md)。

## 许可

[MIT](LICENSE)
