# Stage 1 预检阅读说明

先读 `stage1/linter.md` 与 `stage1/linter.json`，再开 A/B/C 分审。

- 未定义符号：默认 Minor；若该符号出现在损失函数或定理陈述中，升为 Major。
- 过强断言且缺数字、缺引用：Major（overclaim）。
- 结构缺口 `problem_formulation` / `related_work` / `ablation` / `baseline`：Major。
- `variance` / `failure_case`：至少 Minor；若全文无任何重复实验描述则升 Major。
- 否定句（「未做消融」）不得当成已经完成该项工作。
