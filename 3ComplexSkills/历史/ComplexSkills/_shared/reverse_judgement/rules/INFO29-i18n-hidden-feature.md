# INFO29-i18n-hidden-feature 从 i18n 文案反推隐藏功能

负责 skill：`skills/05-js-audit-runtime/SKILL.md`

必须执行规则：`i18n_key,module_guess,admin_hint,route_link`。

输出字段：`js_audit.i18n_signals[]`。

进入 manifest 字段：`js_audit_graph_v4.1.i18n_signals`。

测试样例：`_shared/tests/extreme_reverse_audit/fixtures/i18n-hidden-admin.json`。

预期输出：输出字段必须非空；确实不支持时必须写入 `unsupported_reason`、`source_path` 和 `parser_confidence`。

失败判断：遗漏字段、静默空结果、无路径证据、无质量门槛时失败。

质量门槛：`QG-INFO-coverage-required; missing P0 source blocks top-tier evaluation`。

本机授权边界：只读取本机授权项目和 fixtures；禁止第三方目标探测。
