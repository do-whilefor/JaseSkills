# 漏洞链路真实证据拼接合同

5 条高价值链路只能在每个 evidence node 都有真实来源时进入 `quality_gate_passed`。任何节点缺少文件、路由、请求、响应、认证上下文、角色上下文或租户上下文，链路只能保持 `candidate`、`validation_blocked` 或 `needs_human_review`。
