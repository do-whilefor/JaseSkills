# QUALITY_GATE — hard gate v1

默认 `blocked_until_proven`。没有代码证据、动态证据、负样本、三次复现、合法状态机、影响证明、请求/响应摘要、认证/租户上下文的候选不能进入 confirmed。只有工具告警、只有报错、越界、破坏性验证、拒绝服务、第三方非授权目标一律 rejected 或 validation_blocked。执行器：`scripts/quality_gate_hard_enforcer.py`；策略：`config/quality_gate_hard_policy.json`；测试：`tests/quality_gate_hard_cases.json`。
