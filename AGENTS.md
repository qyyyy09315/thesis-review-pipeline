# 审稿工作区 Agent 约定

本仓库是**高水平本科毕业设计审稿流水线**，不是论文写作仓库。

## 必须调用的技能

- 用户要求审稿 / 评阅 / 挑刺 / 优秀毕设评审：先读并执行 `thesis-review`。
- 输入为中文 LaTeX 学位论文且只需格式/国标检查：可叠加 `latex-thesis-zh`。
- 输入为 SCI/顶会英文稿且用户要期刊级深审：叠加 `paper-audit`。
- DOCX 转 Markdown：`docx-to-markdown`。

## 硬约束

1. **只审不改**：不得直接改写 `papers/` 中的论文源文件。
2. **证据锚定**：每条 Major 必须带章节/公式/图表定位与原文摘引。
3. **不编造文献**：不得虚构 DOI、基线成绩或审稿人原话。
4. **默认离线**：未获用户明确授权不得 `--online` / 文献外搜。
5. **工作日志**：每次 CLI 或实质性审稿步骤必须追加 `docs/worklog.md`。
6. **隐私**：真实学生论文、学号、姓名、学校内部材料不得提交 git。`papers/` 与后续 `runs/` 已被 `.gitignore` 忽略（样例除外）。日志与 metadata 只写相对路径；**提交前必跑 `sanitize` 清洗绝对路径，再跑 `doctor` 确认对账干净**。
7. **深审闭环**：深审完成后把 `consolidator.json` 的 `status` 改为 `done`；预检结构缺口逐项写入 `linter_triage`（accept/reject + 依据），误报不得以 Major 形式进入报告。
8. **跨轮台账**：新发现的 Major/Minor 用 `ledger add` 登记，闭环用 `ledger close`；深审只处理 `ledger list` 中的 open 项与新增项，避免逐轮人肉翻旧报告。
9. **代码–论文对账**：Agent C 填写 `code_correspondence`，把正文和表格中的实验数字、模型结构、超参数、实验设计四类主张逐项对到脚本、配置、日志或结果文件，每行带 `aspect` 与 `paper_ref`（`mismatch` 另附 `paper_quote`）。对不上记 Major（超参纯记录偏差可 Minor）；没有代码则 `code_status=missing`，不得写成已复核；维度不适用须在 `aspects_skipped` 写明理由。作者修订说明不能代替打开结果文件。历史 run 无 `code_status` 时 `doctor` 不追溯。

## Python 环境

本仓库使用项目内 `.venv`（CPython 3.12），禁止用系统 Python 3.14 直接 `pip install`。

```bash
.venv/Scripts/python.exe -m pytest tests -q
.venv/Scripts/python.exe scripts/thesis_review.py init-run papers/<file> --title "题目" --field "专业"
```

重建：`uv venv .venv --python 3.12 && uv pip install -r requirements.txt --python .venv/Scripts/python.exe`

## 入口命令

```bash
.venv/Scripts/python.exe scripts/thesis_review.py init-run papers/<file> --title "题目" --field "专业"
.venv/Scripts/python.exe scripts/thesis_review.py lint ingest/<slug>.md
.venv/Scripts/python.exe scripts/thesis_review.py render runs/<id>
.venv/Scripts/python.exe scripts/thesis_review.py ledger add --severity major --location "<章节>" --problem "<描述>"
.venv/Scripts/python.exe scripts/thesis_review.py ledger close --id M-01 --run <run_id> --note "<闭环依据>"
.venv/Scripts/python.exe scripts/thesis_review.py sanitize
.venv/Scripts/python.exe scripts/thesis_review.py doctor
```
