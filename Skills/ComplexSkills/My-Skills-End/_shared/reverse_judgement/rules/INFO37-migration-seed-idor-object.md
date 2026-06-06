# INFO37-migration-seed-idor-object 从 migration / seed 反推越权对象关系

负责 skill：`skills/04-attack-surface-mapping/SKILL.md`

必须执行规则：`seed_owner,tenant_field,object_relation,cross_actor_path`。

输出字段：`role_object_tenant_ledger.seed_paths[]`。

进入 manifest 字段：`surface_manifest_v2.role_object_tenant_ledger`。

测试样例：`_shared/tests/extreme_reverse_audit/fixtures/seed-idor-object-path.json`。

预期输出：输出字段必须非空；确实不支持时必须写入 `unsupported_reason`、`source_path` 和 `parser_confidence`。

失败判断：遗漏字段、静默空结果、无路径证据、无质量门槛时失败。

质量门槛：`QG-INFO-coverage-required; missing P0 source blocks top-tier evaluation`。

本机授权边界：只读取本机授权项目和 fixtures；禁止第三方目标探测。
