# Stage 3：意见聚合与二稿路线图

读取 A/B/C 的 JSON 与 `stage1/linter.json`，填写 `consolidator.json`，然后运行：

```bash
python scripts/thesis_review.py render runs/<id>
```

## 规则

- 去重：同一根因只保留一条 Major，附上所有定位。
- 机械预检中的未定义符号默认 Minor；若导致损失不可解释则升 Major。
- 缺消融、缺问题形式化、无对照基线 → Major。
- 定级只能是：优秀 / 良好 / 及格 / 退修。
- 机械预检单独不得给「优秀」。
- 每条 Major 必须能映射到路线图中的一条可执行步骤。
