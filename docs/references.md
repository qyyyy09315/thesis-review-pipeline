# 外部参考项目（GitHub / 论文）

检索日期：2026-09-17。本仓库**不 fork**这些项目：它们面向顶会仿真、专用审稿模型或提示词箱，没有中文本科毕设四段合同。吸收的是可落地的机制，不是整仓搬运。

## 最接近、已吸收的点

| 项目 | 星标（检索时） | 性质 | 我们吸收了什么 | 明确不吸收 |
| --- | --- | --- | --- | --- |
| [AliManjotho/open-reviewer](https://github.com/AliManjotho/open-reviewer) | 28 | 多 Agent 预投稿审稿：Parser / Methods / Experiments / Citations / Consistency + scorecard + issue-evidence | 五维评分卡、问题–证据表、HTML 双输出 | OpenCode 运行时、18 个子 Agent、PubPeer 外搜 |
| [FanBroWell/AI-paper-reviewer](https://github.com/FanBroWell/AI-paper-reviewer) | 38 | 顶会自审 prompt 工具箱（10 维 + 4 级红旗） | 过强 claim / 符号一致性 / 红旗分级思路，已映射到 linter 的 OC\* 与 Major/Minor | 段落改写建议（本仓库只审不改） |
| [Ahren09/AgentReview](https://github.com/Ahren09/AgentReview) | 411 | EMNLP 2024 同行评审**仿真**（审稿人/作者/AC 五阶段） | 分角色、再聚合的流程形状（对应我们的 A/B/C + consolidator） | 偏见实验、固定录取率、ICLR 数据 |
| [allenai/marg-reviewer](https://github.com/allenai/marg-reviewer) | 64 | MARG：按章节专精的多 Agent 生成审稿 | 专精 Agent（方法/实验分审）而不是一篇长 prompt | Docker demo、AWS SES、OpenAI 绑定 |
| [maxidl/openreviewer](https://github.com/maxidl/openreviewer) | 17 | NAACL 2025：Llama-OpenReviewer-8B，ICLR 模板 | PDF→Markdown 的必要性（我们已有 ingest） | 自托管 8B 模型、顶会模板替换毕设合同 |
| [ycm824632241/AgentReviewer](https://github.com/ycm824632241/AgentReviewer) | 1 | LangGraph + RAG + FastAPI + Rebuttal | 二审/re-audit 可作为后续（现有 `paper-audit --mode re-audit` 可封装） | Web UI、强制 RAG |

## 论文入口

- MARG: [arXiv:2401.04259](https://arxiv.org/abs/2401.04259)
- AgentReview: [arXiv:2406.12708](https://arxiv.org/abs/2406.12708) · [ACL Anthology](https://aclanthology.org/2024.emnlp-main.70/)
- OpenReviewer: [arXiv:2412.11948](https://arxiv.org/abs/2412.11948) · [ACL Anthology](https://aclanthology.org/2025.naacl-demo.44/)

## 检索过但未采用

- `khaledawwwwwad87-coder/thesis-to-paper-ai-agent`：把学位论文**改写成** Q1 论文，与「只审不改」相反。
- 各类 GitHub PR reviewer（同名 AgentReview）：代码评审，不是学术审稿。
