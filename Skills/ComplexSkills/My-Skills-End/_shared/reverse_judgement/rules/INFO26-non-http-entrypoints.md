# INFO26-non-http-entrypoints webhook / worker / queue / cron / CLI / RPC 入口识别

负责 skill：`skills/04-attack-surface-mapping/SKILL.md`

必须执行规则：`webhook,worker,queue,cron,cli,rpc,consumer`。

输出字段：`attack_surface.non_http_surfaces[]`。

进入 manifest 字段：`surface_manifest_v2.non_http`。

测试样例：`_shared/tests/extreme_reverse_audit/fixtures/non-http-entrypoints.json`。

预期输出：输出字段必须非空；确实不支持时必须写入 `unsupported_reason`、`source_path` 和 `parser_confidence`。

失败判断：遗漏字段、静默空结果、无路径证据、无质量门槛时失败。

质量门槛：`QG-INFO-coverage-required; missing P0 source blocks top-tier evaluation`。

本机授权边界：只读取本机授权项目和 fixtures；禁止第三方目标探测。
