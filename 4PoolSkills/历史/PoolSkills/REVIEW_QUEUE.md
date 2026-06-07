# Review Queue

该文件用于记录不能直接确认的候选风险和需要人工复核的证据缺口。

进入队列的常见原因：

- 目标未提供动态验证环境、账号、租户或登录态。
- evidence manifest 缺少可读脱敏证据或动态 artifacts。
- replay 结果为 `needs_review`、`unavailable`、`needs_manual_target` 或 `not_reproducible`。
- 角色/租户值为占位值。
- 严重风险缺少跨文件 source-sink dataflow、负向控制或阻断控制。

队列项必须保留 finding id、相关文件、证据 id、缺失项、复核建议和不得 confirmed 的原因。
