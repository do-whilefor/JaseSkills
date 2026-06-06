# INFO06-environment-variable 环境变量识别

负责 skill：`skills/02-project-intelligence/SKILL.md`

必须执行规则：`env_name,source_file,classification,secret_redaction_required`。

输出字段：`project_inventory.env_vars[]`。

进入 manifest 字段：`project_inventory_v2.env_vars`。

测试样例：`_shared/tests/extreme_reverse_audit/fixtures/env-vars-redacted.json`。

预期输出：输出字段必须非空；确实不支持时必须写入 `unsupported_reason`、`source_path` 和 `parser_confidence`。

失败判断：遗漏字段、静默空结果、无路径证据、无质量门槛时失败。

质量门槛：`QG-INFO-coverage-required; missing P0 source blocks top-tier evaluation`。

本机授权边界：只读取本机授权项目和 fixtures；禁止第三方目标探测。
