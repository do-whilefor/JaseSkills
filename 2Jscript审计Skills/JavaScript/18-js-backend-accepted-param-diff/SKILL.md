# 18-js-backend-accepted-param-diff

## 定位

本 Skill 专门判断“前端不接受但后端接受”的参数。它把 JS 实际传参、UI 可控字段、TypeScript/interface/schema 暗示字段、API 文档字段、后端 DTO/model/validator/controller 字段、HAR/Burp 实际流量统一比较。

## 触发条件

- 任务要求 Mass Assignment、Over-posting、隐藏参数、只读字段篡改、role/isAdmin/status/tenantId/orgId/userId/ownerId/price/quota/plan/balance/force/debug/dryRun/override 等参数审计。
- 发现前端 disabled、readonly、hidden、feature flag、role guard、tenant guard 字段。
- 发现后端 DTO/model 字段多于前端请求字段。

## 执行步骤

1. 读取 `js_api_parameter_model.json`。
2. 生成 `frontend_sent_fields`、`frontend_schema_fields`、`backend_accept_fields`、`traffic_observed_fields`。
3. 计算 `backend_only_fields`、`frontend_hidden_fields`、`high_risk_backend_only_fields`。
4. 对每个字段生成最小化、非破坏性验证建议：合法对象 vs 无权对象、普通用户 vs 管理员、租户 A vs 租户 B、前端参数 vs 额外参数。
5. 未验证前全部标记为 `candidate-only` 或 `needs_review`。

## 阻断条件

- 无后端源码/文档/schema 且无动态响应证据：不得声称后端接受字段。
- 无响应差异或状态变化证据：不得声称安全影响成立。
- 任何可能修改数据的验证必须使用测试对象、低风险字段、可回滚环境。

## P0 修复后的强制规则：后端接受性必须有请求/响应差异

`js_backend_param_diff.py` 只负责找“前端参数、流量参数、后端 DTO/model/schema 字段”之间的差异候选。它不能证明后端接受额外参数。

要证明后端接受性，必须使用 `js_backend_acceptance_probe.py` 在本机授权测试环境执行最小化、非破坏性对比：baseline request 与 mutated request 必须有请求、响应、角色、租户、对象归属、字段差异、响应差异或状态差异。没有这些证据时，禁止写“后端接受隐藏参数”。
