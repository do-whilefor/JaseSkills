# 16-js-hidden-api-parameter-modeling

## 定位

本 Skill 专门解决 JS 审计中最容易漏掉的两类问题：隐藏接口与隐藏参数。它不把“JS 中出现字符串”直接当成漏洞，而是把前端真实传参、前端类型/schema 暗示、HAR/Burp 实际流量、后端 controller/DTO/model/validator 接受字段放到同一个模型中做差异分析。

## 触发条件

当任务涉及以下内容时必须触发：

- 从 JS、Source Map、bundle、chunk、service worker、HAR 中提取 API。
- 查找隐藏接口、废弃接口、按权限/租户隐藏的接口。
- 查找前端 UI 不暴露、前端不传、disabled/readonly/hidden 但后端可能接受的参数。
- 比对 TypeScript interface、zod/yup schema、OpenAPI、GraphQL variable、后端 DTO/model/schema 的字段差异。
- 判断 Mass Assignment、Over-posting、IDOR、租户字段篡改、role/isAdmin/status/price/quota/force/debug 等高危参数。

## 禁止条件

- 只从 JS 字符串提取到接口时，必须标记为 `candidate-only`。
- 未提供后端源码、DTO/schema/OpenAPI 或动态请求响应证据时，禁止声称“后端已接受额外参数”。
- 未做多角色/多租户对比时，禁止把隐藏参数直接定性为越权。
- 未保存请求、响应、角色、租户、对象 ID、时间、截图或 HAR 证据时，禁止进入 verified 报告。

## 输入

- `js_asset_ledger.json`、JS/TS/Source Map、HAR/Burp 历史、OpenAPI/Swagger/Postman/GraphQL schema。
- 可选后端源码：controller、route、DTO、validator、model、ORM schema、protobuf、zod/yup schema。

## 输出

默认输出到 `reports/js-top-tier/`：

- `js_api_parameter_model.json`：接口、调用文件、方法、路径、协议、参数来源、风险参数、GraphQL/WebSocket/SSE/JSON-RPC 信息。
- `js_backend_param_diff.json`：前端实际传参、UI/TS/schema 暗示参数、后端接受字段、候选隐藏参数、候选 mass assignment 字段。
- `js_severe_candidate_map.json`：把隐藏接口/隐藏参数映射到严重漏洞候选与验证要求。

## 执行步骤

1. 运行 `scripts/js_api_parameter_model.py --ledger reports/js-top-tier/js_asset_ledger.json --root <frontend-root> --backend-root <backend-root> --out reports/js-top-tier`。
2. 运行 `scripts/js_backend_param_diff.py --api-model reports/js-top-tier/js_api_parameter_model.json --out reports/js-top-tier`。
3. 运行 `scripts/js_severe_js_candidate_mapper.py --api-model reports/js-top-tier/js_api_parameter_model.json --param-diff reports/js-top-tier/js_backend_param_diff.json --out reports/js-top-tier`。
4. 将 `candidate_backend_only_fields`、`high_risk_hidden_params`、`role_tenant_params` 交给 `17-js-browser-lazyload-replay` 和 `07-js-dynamic-validator` 做非破坏性验证。

## 参数模型最低字段

每个 API 记录至少包含：`method`、`path`、`baseURL`、`protocol`、`call_file`、`line`、`request_headers`、`query_params`、`path_params`、`body_params`、`form_data_params`、`graphql_operationName`、`graphql_variables`、`websocket_message_types`、`param_sources`、`hidden_param_candidates`、`high_risk_params`、`auth_context`、`tenant_context`、`status`、`evidence`。

## 质量门槛

- 没有 `js_api_parameter_model.json`：隐藏接口与隐藏参数能力最高 35%。
- 没有 `js_backend_param_diff.json`：不得声称发现“前端不接受但后端接受”的参数。
- 没有 HAR/Burp/Playwright replay：不得从候选升级为 verified。
- 没有多角色/多租户差异：所有权限、租户、IDOR、Mass Assignment 只能进入 `needs_review`。
