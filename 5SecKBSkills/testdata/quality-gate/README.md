# Quality Gate 100 条样本集

本样本集用于压测 `quality_gate.py`，共 100 条合成记录：

- 25 条 `promoted`：字段齐全，应通过门禁。
- 35 条 `needs_review`：用于验证未确认记录不会被误升 promoted。
- 20 条 `conflict`：包含冲突字段，必须保留冲突状态。
- 20 条 `rejected`：低可信或无来源，不得进入 promoted。

这些记录均为合成数据，不代表真实漏洞，不得被写入正式 SecKB promoted 区域。
