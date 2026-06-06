# API 规格盘点模板

| API 规格来源 | 文件路径 | 类型 | Method / Operation | Path / Endpoint | 参数摘要 | 是否前端引用 | 是否运行态可达 | 状态 |
|---|---|---|---|---|---|---|---|---|

覆盖对象：OpenAPI、Swagger、Redoc 导出的 JSON/YAML、Postman collection、GraphQL schema/operation、protobuf/gRPC service、RPC schema。

处理规则：规格文件中的接口默认只是静态候选。只有在授权运行态可达、认证/角色/租户影响明确、QG 评分通过后，才能进入报告发现。过期文档、仅测试 collection、mock server 路由必须写入不可报告或待确认原因。
