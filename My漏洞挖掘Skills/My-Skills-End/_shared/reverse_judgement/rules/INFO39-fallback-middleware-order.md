# INFO39-fallback-middleware-order 从 fallback route / catch-all / middleware 顺序反推认证绕过

负责 skill：`skills/03-code-knowledge-graph/SKILL.md`

必须执行规则：`catch_all_route,order,auth_optional,shadow_route`。

输出字段：`security_graph.middleware_order_findings[]`。

进入 manifest 字段：`security_graph_v3.edges`。

测试样例：`_shared/tests/extreme_reverse_audit/fixtures/catchall-middleware-order.json`。

预期输出：输出字段必须非空；确实不支持时必须写入 `unsupported_reason`、`source_path` 和 `parser_confidence`。

失败判断：遗漏字段、静默空结果、无路径证据、无质量门槛时失败。

质量门槛：`QG-INFO-coverage-required; missing P0 source blocks top-tier evaluation`。

本机授权边界：只读取本机授权项目和 fixtures；禁止第三方目标探测。
