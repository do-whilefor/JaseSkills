# INFO40-legacy-mobile-electron-extension 兼容/mobile/小程序/Electron/extension API 遗留暴露面

负责 skill：`skills/05-js-audit-runtime/SKILL.md`

必须执行规则：`legacy_api,mobile_api,miniapp_api,electron_ipc,extension_script`。

输出字段：`js_audit.legacy_cross_platform_surfaces[]`。

进入 manifest 字段：`js_audit_graph_v4.1.cross_platform`。

测试样例：`_shared/tests/extreme_reverse_audit/fixtures/legacy-mobile-electron-extension.json`。

预期输出：输出字段必须非空；确实不支持时必须写入 `unsupported_reason`、`source_path` 和 `parser_confidence`。

失败判断：遗漏字段、静默空结果、无路径证据、无质量门槛时失败。

质量门槛：`QG-INFO-coverage-required; missing P0 source blocks top-tier evaluation`。

本机授权边界：只读取本机授权项目和 fixtures；禁止第三方目标探测。
