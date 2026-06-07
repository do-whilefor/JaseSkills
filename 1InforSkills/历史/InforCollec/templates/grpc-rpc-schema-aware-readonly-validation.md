# gRPC / RPC schema-aware 只读验证模板

用途：在本机或明确授权服务范围内，对 gRPC、JSON-RPC、XML-RPC、tRPC、自定义 RPC 的信息暴露面进行 schema-aware 只读验证。该模板是“基于文档延伸”，服务于原文档中对 RPC / gRPC 暴露、运行态验证、动态证据、不可报告原因的要求。

## 必须调用

当候选资产、源码、前端 bundle、OpenAPI/GraphQL/RPC 定义、proto/IDL、反向代理配置、端口枚举或错误响应中出现以下信号时调用：

- `.proto`、`grpc`、`grpcurl`、`reflection`、`protobuf`、`buf.yaml`、`buf.gen.yaml`
- JSON-RPC、XML-RPC、tRPC、RPC endpoint、method name、service name
- `Content-Type: application/grpc`、`application/json-rpc`、`application/x-protobuf`
- WebSocket/RPC 混合协议、SSE/RPC 通道、Gateway 转发到 RPC 服务

## 禁止调用

- 目标不是本机、容器网络或明确授权地址。
- 用户要求调用写入、删除、创建、更新、发送、转账、重置、邀请等有副作用方法。
- 没有 schema/IDL/proto/文档/错误响应线索，却要求暴力枚举方法。
- 要求用真实 token 调外部 API 验证。
- 要求压测、爆破字段、枚举公网服务。

## 输入

- 资产编号：`asset_id`
- 端点：`host:port`、HTTP RPC URL、WebSocket RPC URL
- 协议类型：gRPC / JSON-RPC / XML-RPC / tRPC / custom RPC / unknown
- schema 来源：proto、IDL、docs、代码生成文件、前端 bundle、错误响应、测试集合
- 授权边界：本机 / 容器网络 / 明确授权内网
- 认证上下文：未认证 / 低权限 / 指定测试账号 / 不可用
- 只读方法 allowlist：由用户或 schema 明确确认为只读的方法列表

## 最小执行路径

1. 确认目标属于授权范围。
2. 从源码或配置定位 schema/IDL/proto/文档来源。
3. 只提取 service、message、method、field 名称，不调用业务方法。
4. 对 gRPC 优先执行 reflection/list/describe 类只读元数据验证；如果服务未开启 reflection，则只记录“未开启 reflection”，不要强行调用业务方法。
5. 对 JSON-RPC/XML-RPC/tRPC 只验证 endpoint 是否存在、Content-Type、错误体、允许方法提示、schema 影子线索。
6. 如果要调用方法，必须同时满足：方法在 allowlist 中、语义只读、参数为空或使用文档提供的安全只读参数、用户授权、不会改变数据。
7. 所有响应只记录摘要、字段名、类型、长度、hash、错误扩展，不输出完整敏感内容。
8. 结果回填资产账本，状态只能是：已验证元数据暴露 / 静态候选 / 待确认 / 不可报告。

## 专家执行路径

1. 建立 schema 指纹：service、package、method、message、field、enum、版本、生成器、文件路径。
2. 对比四类来源：源码 schema、前端引用、运行态错误、文档接口。
3. 检查 reflection 是否暴露 service 列表。
4. 检查错误体是否泄露 resolver、handler、service path、method suggestion、field suggestion、trace id、stack、internal host。
5. 对不同角色复测同一 RPC endpoint 的错误体和元数据差异。
6. 将每个差异写入“为什么可疑 / 为什么能或不能报告”。

## 允许的工具

工具不是必须存在。不存在时不得编造结果。

- `grpcurl`：只允许 `list`、`describe`，默认不调用业务方法。
- `buf` / `protoc`：只允许本地 schema 解析，不生成或执行客户端。
- `curl`：只允许低频 HTTP metadata、OPTIONS、错误格式验证。
- 项目内已有测试集合：只读读取，不执行写入测试。

## gRPC 安全命令样例

```bash
# 仅在本机或授权 host 使用。list/describe 属于元数据读取。
grpcurl -plaintext 127.0.0.1:50051 list
grpcurl -plaintext 127.0.0.1:50051 describe package.Service
```

禁止默认执行：

```bash
# 禁止：未确认只读语义前不得调用业务方法
grpcurl -d '{...}' 127.0.0.1:50051 package.Service/CreateUser
```

## 输出

| 字段 | 说明 |
|---|---|
| asset_id | 资产编号 |
| protocol | gRPC/RPC 类型 |
| endpoint | 脱敏端点 |
| schema_source | proto/IDL/docs/error/frontend/test |
| runtime_metadata | service/method/field 摘要 |
| auth_state | 认证状态 |
| role | 角色 |
| evidence_id | 证据编号 |
| risk | 风险 |
| status | 已验证/待确认/不可报告 |
| why_suspicious | 为什么可疑 |
| why_reportable_or_not | 为什么能/不能报告 |

## 不可报告原因

- 只有本地 proto 文件，运行态 endpoint 不可访问。
- reflection 关闭，错误体无敏感信息。
- 需要管理员权限且属于预期可见。
- 方法可能有副作用，未调用。
- 没有影响证明。
- 超出授权范围，未验证。
