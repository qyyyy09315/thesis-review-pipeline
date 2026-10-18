# 贡献

## 分支和提交

从 `main` 拉分支。提交说明用约定式：

```text
feat(delivery): 总览把类型和状态分开
fix(scope): 未登记路径走发布检查
docs: 补 PR 模板
```

类型用 `feat`、`fix`、`docs`、`test`、`refactor`、`chore`、`ci`、`perf`、`build`。范围可省略。

## Pull request

用仓库自带的模板。正文要有这几个标题：摘要、动机、改动、测试、决定、隐私。

决定只写这一 PR 回答的那一件事，不要写成全项目通过或不通过。

隐私一节默认写「不含个人稿件与具体审稿记录」。个人稿件、学号、姓名和某一篇的审稿摘录、台账、工作日志都不要放进 PR。确实要带时，删掉这句，改成「已脱敏」或「已获授权」，并写清范围。没写这三句之一，检查不会通过。

建议对象里必须 @ 一位开发者，或一个开发者组。组的写法是 `@org/team`，例如 `@acme/review-pipeline`。只写名字、不带 `@`，检查不会通过。邮件地址也不算。

CI 里的 `pr-format` 会跑 `python scripts/pr_check.py`，只读 `PR_TITLE` 和 `PR_BODY`，不装审稿依赖。本地装好依赖后也可以跑 `python scripts/thesis_review.py pr-check`。

`.github/CODEOWNERS` 把评审请求指到维护者。若要 GitHub 自动请求，在分支保护里打开 “Require review from Code Owners”。新增模块时，把对应目录加给负责的人或组。

## 检查跑多少

稳定入口：

```bash
python scripts/thesis_review.py check
```

只改了已知范围时，先看影响：

```bash
python scripts/thesis_review.py scope --changed scripts/ingest.py
```

依赖没变的部分沿用已有证据。碰到清单里没有的路径，按发布点做全量检查。不要在审稿目录里复制一份临时脚本当成长期测试；要留下的检查进这个仓库的 `tests/`。
