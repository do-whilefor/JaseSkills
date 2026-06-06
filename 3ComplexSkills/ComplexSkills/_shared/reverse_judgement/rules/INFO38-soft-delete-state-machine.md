# INFO38-soft-delete-state-machine 从软删除归档状态机字段反推边界绕过路径

负责 skill：`skills/04-attack-surface-mapping/SKILL.md`

必须执行规则：`soft_delete_field,archive_field,state_field,transition_guard`。

输出字段：`attack_surface.state_boundary_surfaces[]`。

进入 manifest 字段：`surface_manifest_v2.state_boundaries`。

测试样例：`_shared/tests/extreme_reverse_audit/fixtures/state-machine-boundary.json`。

预期输出：输出字段必须非空；确实不支持时必须写入 `unsupported_reason`、`source_path` 和 `parser_confidence`。

失败判断：遗漏字段、静默空结果、无路径证据、无质量门槛时失败。

质量门槛：`QG-INFO-coverage-required; missing P0 source blocks top-tier evaluation`。

本机授权边界：只读取本机授权项目和 fixtures；禁止第三方目标探测。
