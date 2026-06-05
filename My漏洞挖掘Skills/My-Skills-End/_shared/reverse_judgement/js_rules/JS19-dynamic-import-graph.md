# JS19-dynamic-import-graph dynamic import 图

负责 skill：`skills/05-js-audit-runtime/SKILL.md`

AST / parser 要求：`ImportExpression edge mapping`。

输出字段：`symbol_graph.dynamic_import_edges[]`。

候选漏洞联动：`C03,C22`。

进入 manifest 字段：`js_graph.symbol_graph`。

测试样例：`_shared/tests/extreme_reverse_audit/fixtures/js-dynamic-import-graph.json`。

预期输出：提取结果必须能追踪到 JS source、chunk/hash、source span；若进入漏洞候选，必须产生 `candidate_to_manifest_link`。

失败判断：无法追踪 JS -> candidate -> evidence manifest -> quality gate -> report section 时失败。

质量门槛：`QG-JS-chain-required; JS-derived confirmed finding must have candidate_to_manifest_link, original span when sourcemap exists, and template-specific evidence`。

本机授权边界：只分析本机授权项目中的源码、构建产物、sourcemap 和 fixtures；CDN URL 只记录引用，不主动访问第三方。
