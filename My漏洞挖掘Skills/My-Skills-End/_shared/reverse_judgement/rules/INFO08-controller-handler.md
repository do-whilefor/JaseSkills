# INFO08-controller-handler 控制器识别

负责 skill：`skills/03-code-knowledge-graph/SKILL.md`

必须执行规则：`handler_symbol,class_or_function,source_span,call_targets`。

输出字段：`security_graph.handlers[]`。

进入 manifest 字段：`security_graph_v3.nodes`。

测试样例：`_shared/tests/extreme_reverse_audit/fixtures/controller-handler-symbol.json`。

预期输出：输出字段必须非空；确实不支持时必须写入 `unsupported_reason`、`source_path` 和 `parser_confidence`。

失败判断：遗漏字段、静默空结果、无路径证据、无质量门槛时失败。

质量门槛：`QG-INFO-coverage-required; missing P0 source blocks top-tier evaluation`。

本机授权边界：只读取本机授权项目和 fixtures；禁止第三方目标探测。
