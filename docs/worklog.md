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

仓库：http<本地路径> （public）。样例 run 公开；`papers/` 与后续 `runs/` 默认忽略，避免真实论文入库。

## 2026-09-17 12:34:35

render `20260917-112554-sample_thesis` → `runs/20260917-112554-sample_thesis/review_report.md`

## 2026-09-17 会话：完善 README

重写根目录 `README.md`，面向编码 Agent 工作区（ZCode / Codex / WorkBuddy 等），保留 CLI 独立用法。

- 补适用范围、给 Agent 的入口、run 产物、报告合同、Unix 解释器路径。
- 增加徽章、目录、mermaid 流程图；不改论文源文件与流水线代码。
- 语言按 `qu-ai-wei` / `lieflat-less-ai-tone` 压过：去掉「不是……而是」翻案腔与过密顿号罗列，维持公文/技术说明语体。


## 2026-09-18 13:08:40

init-run `draft_real.md` → `20260918-130840-draft_real`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_real.md`
- linter: `runs/20260918-130840-draft_real/stage1/linter.json`

## 2026-09-18 13:12:12

render `20260918-130840-draft_real` → `runs/20260918-130840-draft_real/review_report.md`

## 2026-09-18 13:13:17

真实实验重跑稿深审 `20260918-130840-draft_real`，定级 良好（4 Major）

- 输入: `ingest/draft_real.md`（由初稿.docx 文本抽取，未 git）
- 报告: `runs/20260918-130840-draft_real/review_report.md`
- 诚实转向已核：旧虚构串 76.46/95.97/186/28.4/99.32 计数为 0；48k F1=62.03，零样本低于随机线，注意力恒等已写入第五章
- 残留 Major：3.5 与消融互斥；系统 36D joblib vs 75D 主模型；6.1 +5.95；4.7 20项 vs 9条/工业级
- 只审不改 papers/；未 --online；未 git add

## 2026-09-19 07:59:46

init-run `draft_v8.md` → `20260919-075946-draft_v8`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v8.md`
- linter: `runs/20260919-075946-draft_v8/stage1/linter.json`

## 2026-09-19 08:00:50

render `20260919-075946-draft_v8` → `runs/20260919-075946-draft_v8/review_report.md`

## 2026-09-19 08:01:03

对账稿深审 20260919-075946-draft_v8，定级 良好（残留 1 Major）

- 输入: ingest/draft_v8.md（初稿.docx 文本抽取，未 git）
- 报告: runs/20260919-075946-draft_v8/review_report.md
- 第四轮 4 Major/5 Minor 主体关闭；残留 1 Major：1.3 抑制累积噪声 + 4.1/4.2 仍承诺在线 CNN
- 只审不改 papers/；未 online；未 git add

## 2026-09-19 08:19:41

init-run `draft_v9.md` → `20260919-081941-draft_v9`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v9.md`
- linter: `runs/20260919-081941-draft_v9/stage1/linter.json`

## 2026-09-19 08:20:51

render `20260919-081941-draft_v9` → `runs/20260919-081941-draft_v9/review_report.md`

## 2026-09-19 08:20:51

对账稿深审 20260919-081941-draft_v9，定级 良好（0 Major）

- 输入: ingest/draft_v9.md
- 报告: runs/20260919-081941-draft_v9/review_report.md
- 上轮 1 Major 已关；0 Major；残留 Minor：150并发写成实测、4.7.1仍双份、表4.1 Vue.js
- 只审不改；未 online；未 git add

## 2026-09-19 08:42:55

init-run `draft_v10.md` → `20260919-084255-draft_v10`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v10.md`
- linter: `runs/20260919-084255-draft_v10/stage1/linter.json`

## 2026-09-19 08:43:49

render `20260919-084255-draft_v10` → `runs/20260919-084255-draft_v10/review_report.md`

## 2026-09-19 08:43:49

对账稿深审 20260919-084255-draft_v10，定级 良好（0 Major，点名 Minor 已清）

- 输入: ingest/draft_v10.md
- 报告: runs/20260919-084255-draft_v10/review_report.md
- 4 条 Minor 全关；150 并发 TPS 148.4 与压测 CSV 一致；0 Major
- 只审不改；未 online；未 git add

## 2026-09-19 08:50:47

init-run `draft_v11.md` → `20260919-085047-draft_v11`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v11.md`
- linter: `runs/20260919-085047-draft_v11/stage1/linter.json`

## 2026-09-19 08:52:12

render `20260919-085047-draft_v11` → `runs/20260919-085047-draft_v11/review_report.md`

## 2026-09-19 08:52:12

对账稿深审 20260919-085047-draft_v11，定级 良好（关键词对齐，可答辩）

- 输入: ingest/draft_v11.md
- 报告: runs/20260919-085047-draft_v11/review_report.md
- 关键词与 1.3 其三已对齐；0 Major；可答辩
- 只审不改；未 online；未 git add

## 2026-09-19 11:03:03

init-run `draft_v12.md` → `20260919-110303-draft_v12`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v12.md`
- linter: `runs/20260919-110303-draft_v12/stage1/linter.json`

## 2026-09-19 11:04:20

render `20260919-110303-draft_v12` → `runs/20260919-110303-draft_v12/review_report.md`

## 2026-09-19 11:04:20

对账稿深审 20260919-110303-draft_v12，定级 良好（2 Major：方法章与分析段未随级联拼接更新）

- 输入: ingest/draft_v12.md
- 报告: runs/20260919-110303-draft_v12/review_report.md
- 主表与 final_v2 CSV 对齐；3.5/5.4/5.5/5.8/英文摘要未跟级联拼接修正
- 2 Major；只审不改；未 online；未 git add

## 2026-09-19 11:22:14

init-run `draft_v13.md` → `20260919-112214-draft_v13`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v13.md`
- linter: `runs/20260919-112214-draft_v13/stage1/linter.json`

## 2026-09-19 11:23:20

render `20260919-112214-draft_v13` → `runs/20260919-112214-draft_v13/review_report.md`

## 2026-09-19 11:23:20

对账稿深审 20260919-112214-draft_v13，定级 良好（0 Major，可答辩）

- 输入: ingest/draft_v13.md
- 报告: runs/20260919-112214-draft_v13/review_report.md
- 上轮 2 Major 已关；0 Major；残留 1.3/3.5 独立训练起句、5.3 差 3.49
- 只审不改；未 online；未 git add

## 2026-09-19 11:53:42

init-run `draft_v14.md` → `20260919-115342-draft_v14`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v14.md`
- linter: `runs/20260919-115342-draft_v14/stage1/linter.json`

## 2026-09-19 11:54:45

render `20260919-115342-draft_v14` → `runs/20260919-115342-draft_v14/review_report.md`

## 2026-09-19 11:54:45

对账稿深审 20260919-115342-draft_v14，定级 良好（1 Major：关注意力后主数字未统一）

- 输入: ingest/draft_v14.md
- 报告: runs/20260919-115342-draft_v14/review_report.md
- 曾探索旁白可删；Major：99.32/99.29/99.35 三套主分数未锁
- 只审不改；未 online；未 git add

## 2026-09-19 14:27:44

init-run `draft_v15.md` → `20260919-142744-draft_v15`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v15.md`
- linter: `runs/20260919-142744-draft_v15/stage1/linter.json`

## 2026-09-19 14:29:03

render `20260919-142744-draft_v15` → `runs/20260919-142744-draft_v15/review_report.md`

## 2026-09-19 14:29:03

对账稿深审 20260919-142744-draft_v15，定级 良好（v14 Major 关闭；新 Major 窗口 L=1024 与主表不一致）

- 输入: ingest/draft_v15.md
- 对照: doc/12_REVISION_NOTES_v15.md（工程侧）
- v14 Major 已关；新 Major：表5.5 L=1024 F1=90.38 vs 主表 99.32
- 只审不改；未 online；未 git add

## 2026-09-20 08:14:04

init-run `draft_v16.md` → `20260920-081404-draft_v16`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v16.md`
- linter: `runs/20260920-081404-draft_v16/stage1/linter.json`

## 2026-09-20 08:14:53

render `20260920-081404-draft_v16` → `runs/20260920-081404-draft_v16/review_report.md`

## 2026-09-20 08:14:53

对账稿深审 20260920-081404-draft_v16，定级 良好（v15 清单闭环，0 Major，可答辩）

- 输入: ingest/draft_v16.md
- 对照: 工程侧 doc/13_REVISION_NOTES_v16.md
- v15 1 Major + 5 Minor 闭环；0 Major；残留 SHAP 3.09 vs CSV 3.18、英文 L 口径
- 只审不改；未 online；未 git add

## 2026-09-20 09:10:49

init-run `draft_v17.md` → `20260920-091049-draft_v17`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v17.md`
- linter: `runs/20260920-091049-draft_v17/stage1/linter.json`

## 2026-09-20 09:11:33

render `20260920-091049-draft_v17` → `runs/20260920-091049-draft_v17/review_report.md`

## 2026-09-20 09:11:33

对账稿深审 20260920-091049-draft_v17，定级 良好（0 Major；48k 等时长写入；5.5/5.8 两处笔误）

- 输入: ingest/draft_v17.md
- 对照: 工程侧 doc/14_REVISION_NOTES_v17.md
- v16 三条 Minor 主体关闭；48k 等时长 CSV 对齐 80.97；新 Minor：21.1 安错指标、5.8 未吸收等时长
- 只审不改；未 git add

## 2026-09-20 09:34:19

init-run `draft_v18.md` → `20260920-093419-draft_v18`，定级 退修，报告 `review_report.md`

- ingest: `ingest/draft_v18.md`
- linter: `runs/20260920-093419-draft_v18/stage1/linter.json`

## 2026-09-20 09:34:54

render `20260920-093419-draft_v18` → `runs/20260920-093419-draft_v18/review_report.md`

## 2026-09-20 09:34:54

对账稿深审 20260920-093419-draft_v18，定级 良好（v17 三处文字已关，0 Major）

- 输入: ingest/draft_v18.md
- 源: papers/初稿.docx
- v17 三条 Minor 抽取核验关闭；0 Major；可答辩
- 只审不改；未 git add


## 2026-09-20 会话：v19 补充实验纳入/留档判定（论文未改）

作者侧已跑完三项可选实验，`初稿.docx` 本轮未改。审稿侧独立核对 CSV 后给出写入口径，未改 `papers/`、未改工程正文。

核对文件：
- `工程侧/results/final_v2/12k_stratified_foldmean.csv`
- `工程侧/results/final_v2/12k_or007_014_errors.csv`
- `工程侧/results/final_v2/table5_6b_alignment_xecml.csv`
- `工程侧/results/final_v2/table5_6c_frozen_head.csv`
- `工程侧/results/final_v2/main_model_noattn.csv`
- 报告：`工程侧/doc/18_EXPERIMENT_REPORT_v19.md`

判定：
1. 12k 位置/尺寸分层 + 1 例方位混：纳入 5.3（一句 + 表5.3b）。16 类 99.32±0.77 与主模型锁定值一致。
2. 跨台架 Z-score/CORAL 零样本对齐：仅留档，不进表5.6。全部 F1<33.33；CORAL 对 36D/75D 同向提升，不得写「CNN 是台架指纹」。无对齐 75D F1=6.40 与表5.6 的 5.68 非同一脚本，禁止并表。
3. 冻结主干+线性头 10%：纳入 6.2 一句部署方向。75D F1 88.61±14.74，低于全量重拟合 96.43，不得作为表5.6 新行。

只审不改；未 git add。

## 2026-09-20 会话：v19 落稿抽取复审（只审不改）

作者已将 12k 分层与 6.2 补充句写入 `初稿.docx`（10:11）。审稿侧 python-docx 纯文本抽取 `ingest/draft_v19.md`，与 CSV 对账。未改论文源文件，未装配。

抽取核验：
- 表5.3b 数字与 `12k_stratified_foldmean.csv` 一致（99.32/99.75/99.02）
- 6.2 CORAL F1 28.34/23.87 与 `table5_6b_alignment_xecml.csv` 一致；冻结头 88.61/78.03 与 `table5_6c_frozen_head.csv` F1 列一致
- 表5.6 未并入对齐实验；无「曾探索」旁白
- 未关：5.3 图5.3 评述仍写「0.007 与 0.014 外圈方位边界」，CSV 仅 1 例 0007_Centered→Opposite
- 未关：6.2 将冻结主干写成与「显式特征提供不变边界、深度表征负责快速适配」同向，超出对齐实验支持范围

定级维持 良好。0 新 Major；2 条文字 Minor。只审不改；未 git add。
## 2026-09-20 10:32:31

ingest `初稿.docx` → `ingest/初稿.md`


## 2026-09-20 会话：v20 抽取复审（M1/M2）

作者称 9 处文字改动已写入 5.3/6.2。审稿侧对 `papers/初稿.docx`（10:32）python-docx 重抽 `ingest/draft_v20.md`，不采信 `doc/19_REVISION_NOTES_v20.md`。

核验：
- M1 关闭：旧串「0.007 英寸与 0.014 英寸外圈方位边界」MISS；OOF 1 例 `0007_Centered→0007_Opposite` HIT；P3B「未观察到损伤尺寸维度的系统性混淆」HIT
- M2 关闭：旧串「显式特征提供不变边界 / 深度表征负责快速适配」在 6.2 MISS；88.61 对照表5.6 的 96.43 HIT；「不列入表5.6」HIT
- 数字与 CSV 一致：99.75/99.02/28.34/23.87/88.61/78.03；主结果 99.32、80.97、5.68 仍在
- 5.6 第三段「台架特异性 / 显式物理特征提供跨台架不变边界」仍在（本轮未要求改 5.6）
- 无「曾探索」

定级维持 良好，0 Major，v19 两条 Minor 抽取关闭。只审不改；未 git add。
## 2026-09-20 10:48:32

ingest `初稿.docx` → `ingest/初稿.md`


## 2026-09-20 会话：开题报告 vs 现稿结构是否回写

只审不改。开题为本地 `.doc`（OLE），antiword 抽至 `ingest/kaiti_extract.md`（gitignore）。论文对照 `ingest/draft_v20.md`。

结论：不必因现稿目录增补（表5.3a/5.3b、48k 等时长、CORAL/冻结头）整份重开题。题目与六条主线仍覆盖。唯一需主动说明的方法差异是开题将「自注意力动态加权」列为技术关键，现稿主模型已去掉（关键词为层间概率拼接；正文 0 处「自注意力」）。系统由开题 Streamlit 改为 FastAPI 四层，属实现路径细化。建议准备一页「与开题差异说明」而非改开题历史文本，除非学院强制开题-论文逐条一致。

日志不写姓名学号。未 git add。
## 2026-09-20 10:55:09

ingest `初稿.docx` → `ingest/初稿.md`

## 2026-09-20 11:04:39

ingest `初稿.docx` → `ingest/初稿.md`

## 2026-09-20 11:17:05

ingest `初稿.docx` → `ingest/初稿.md`

## 2026-09-20 会话：doctor 对账补录（7 个早期 run 缺日志）

doctor 对账发现以下 run 在本日志中无记录，现按 `runs/<id>/metadata.json` 补录。
该批 run 早于日志规范落地，均为同一真实稿的连续迭代（深审意见经后续轮次闭环，
详见 2026-09-18 13:13 起的 draft_real / draft_v8 各条深审记录）。

| run id | created_at | 说明 |
| --- | --- | --- |
| `runs/20260917-124646-初稿` | 2026-09-17T12:46:46 | `papers/初稿.docx` 首次 init-run；标题行被 docx 转换为内嵌图片，metadata.title 提取为 raw markdown（已知缺陷） |
| `runs/20260917-125030-draft_text` | 2026-09-17T12:50:30 | 纯文本抽取稿 init-run |
| `runs/20260917-133834-draft_v2` | 2026-09-17T13:38:34 | v2 迭代 init-run |
| `runs/20260918-075923-draft_v3` | 2026-09-18T07:59:23 | v3 迭代 init-run |
| `runs/20260918-081013-draft_v4` | 2026-09-18T08:10:13 | v4 迭代 init-run |
| `runs/20260918-082439-draft_v5` | 2026-09-18T08:24:40 | v5 迭代 init-run |
| `runs/20260918-083303-draft_v6` | 2026-09-18T08:33:03 | v6 迭代 init-run |

定级一列均为机械预检阶段的旧默认「退修」（修复前的占位语义，非深审结论）。
只审不改；未 online；未 git add。

## 2026-09-20 15:23:56

sanitize 清洗绝对路径 9 处（docs/worklog.md 等）

## 2026-09-20 15:25:10

ledger add N-01：5.6 第三段 — 「台架特异性 / 显式物理特征提供跨台架不变边界」表述超出对齐实验支持范围，v20 会话标记本轮未要求改，仍待收敛。

## 2026-09-20 15:25:10

render `20260920-093419-draft_v18` → `runs/20260920-093419-draft_v18/review_report.md`


## 2026-09-20 会话：工作流体检与全量修复（代码未触论文）

体检发现并修复 7 项问题，测试 12 → 28 passed：

1. P0 render 回退 bug：`consolidator.status == done` 时 `majors/minors` 空列表表示「深审确认无」，不再回退 `_majors_from_lint` 机械兜底。v18 报告重渲染后假 Major（结构缺口/problem_formulation）已消除，如实显示「深审确认：无 Major」。模板二/三节空列表文案按 `deep_done` 区分；`scorecard.render_html` 同步。
2. init-run 定级语义：`metadata.grade` 改记「待深审」，机械建议存 `grade_suggested`；consolidator 模板默认 `grade` 由「退修」改为 null。消除「每轮 init-run 定级退修 → 深审良好」的日志噪声。
3. 深审预检对账：`consolidator.json` 新增 `linter_triage`（accept/reject + 依据），报告新增「Stage 1 机械预检对账」表，reject 的误报不得进报告。合同见 `templates/agents/consolidator.md`。
4. 跨轮台账：新增 `ledger add/close/list` 子命令与 `docs/ledger.json`（M-/N- 前缀编号），render 自动附「跨轮遗留」表。首批登记 N-01（5.6 第三段表述超出对齐实验支持范围，v20 会话遗留）。修复 `next_id` 前缀解析 bug（`int("-01")` 导致编号停在 01，测试抓出）。
5. 隐私与对账：新增 `sanitize` 子命令（worklog 绝对路径 → `papers/初稿.docx` / `工程侧/...` 相对写法，已清洗 9 处）；新增 `doctor` 子命令（run-日志对账、绝对路径泄漏、consolidator 状态校验，当前全绿）；7 个早期 run 已按 metadata 补录日志。
6. ingest 版本化：`ingest --versioned` 输出时间戳后缀文件名，同名覆盖丢版本的问题关闭。
7. linter 中文信号词典扩充：六类结构缺口各补真实工科 docx 抽取稿常见写法；v18 真实稿结构缺口 6 → 0，机械定级与深审「良好」背离根除。

新增 `.github/workflows/ci.yml`（pytest + doctor）；README / AGENTS.md / thesis-review SKILL.md 已同步新命令与合同。只审不改；未 online。

## 2026-09-22 会话：实验数字必须对上代码

深审不再只看实验章节和修订说明。Agent C 新增必填 `code_correspondence`：主结果、消融和正文增益逐条对到脚本、配置、日志或结果文件。

- `code_status`：`pending` / `missing` / `partial` / `checked`。`mismatch` 记 Major；没有代码则 `missing`，定量主张不得写成已复核。
- `doctor` 在 `consolidator.status=done` 时检查该字段。没有 `code_status` 的历史 run 不追溯，当前工作区 doctor 仍为全绿。
- 合同写入 `templates/agents/agent_c_experiments.md`、`consolidator.md`、`AGENTS.md`、`README.md`，以及 `.agents` / `.zcode` / 用户级 `thesis-review` 技能。
- 测试 32 passed。只审不改；未改 `papers/`。
