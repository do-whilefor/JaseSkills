# GraphQL 非破坏验证模板

本模板用于在授权本机项目中，对 GraphQL 入口进行只读、低频、非破坏的信息暴露验证，尤其处理 introspection 关闭时的错误富信息、schema 影子线索、字段名泄露和 resolver/内部路径泄露。

## 适用场景

- 发现 `/graphql`、`/graphiql`、`/playground`、`/api/graphql` 或前端 bundle 中的 GraphQL 请求。
- OpenAPI 不存在，但前端代码出现 `query`、`mutation`、`gql`、Apollo、Relay、urql。
- introspection 关闭或不可访问，但错误响应可能泄露类型、字段、resolver、路径、扩展信息。
- 需要比较未认证、低权限、管理员视角下 GraphQL 错误和响应差异。

## 禁止场景

- 不执行 mutation。
- 不爆破字段名、类型名、对象 ID。
- 不大规模枚举 schema。
- 不发送破坏性 payload。
- 不访问非授权 GraphQL 服务。
- 不把 GraphQL 错误消息直接当成确定暴露，必须进入动态验证和质量门禁。

## 最小非破坏验证路径

1. 确认 GraphQL endpoint 属于本机授权项目。
2. 记录 endpoint、认证状态、角色标签。
3. 发送 `OPTIONS` 或等价只读方法，记录 Allow、CORS、Content-Type、Server、缓存头。
4. 发送最小只读 query：`{ __typename }`，用于确认是否为 GraphQL 响应。
5. 发送格式错误但非破坏请求，观察错误体是否包含 stack、path、extensions、serviceName、code、字段建议。
6. 发送不存在字段的只读 query，例如 `{ __infoExposureProbeNonexistentField }`，观察是否返回 “Did you mean”、类型名、字段名、schema 片段。
7. 如果文档或用户明确授权 introspection，才可执行 introspection；默认不执行。
8. 对不同角色重复相同只读请求，比较错误字段、响应大小、extensions、状态码差异。
9. 将 GraphQL 候选结果交给 04 动态验证，再交给 07 质量门禁。

## 可选脚本路径

```bash
./scripts/graphql-nondestructive-probe.sh \
  --endpoint http://127.0.0.1:3000/graphql \
  --out graphql-probe.md
```

授权内网主机必须显式允许：

```bash
./scripts/graphql-nondestructive-probe.sh \
  --endpoint http://app.internal:8080/graphql \
  --allow-host app.internal \
  --out graphql-probe.md
```

携带授权测试 token 时，必须使用本机授权测试账号，并且不要在输出中记录完整 token：

```bash
./scripts/graphql-nondestructive-probe.sh \
  --endpoint http://127.0.0.1:3000/graphql \
  --header 'Authorization: Bearer ****' \
  --out graphql-probe-user.md
```

## 输出格式

```md
# GraphQL 非破坏验证结果

## 入口确认
- Endpoint：
- 来源：源码 / 前端 bundle / 文档 / 运行态发现
- 认证状态：
- 角色：
- 是否授权范围内：

## 请求摘要
| 编号 | 请求类型 | 方法 | 状态码 | 响应大小 | Content-Type | 关键头 | 是否包含错误富信息 |
|---|---|---|---:|---:|---|---|---|

## 错误富信息
| 编号 | 错误字段 | 脱敏摘要 | 泄露类型 | 是否敏感 | 下一步验证 |
|---|---|---|---|---|---|

## Schema 影子线索
| 来源 | 字段/类型/路径线索 | 证据 | 可信度 | 是否需要动态验证 |
|---|---|---|---|---|

## 角色差异
| 请求 | 未认证 | 普通用户 | 低权限 | 管理员 | 差异摘要 | 结论 |
|---|---|---|---|---|---|---|

## 不可报告原因
-
```

## 质量门槛

- 只读 query 和错误富信息只能产生候选，不能直接成为确定发现。
- mutation 必须禁止，除非用户明确要求且属于非破坏测试环境；默认仍不执行。
- 没有动态 endpoint 和响应摘要时，只能标记为静态候选。
- 如果只得到 “introspection disabled”，没有额外信息泄露，则不可报告。
- 如果错误信息只对管理员可见且符合预期，默认不可报告。

##

该模板是基于原文 “GraphQL 暴露”“GraphQL error extensions”“文档影子法”“错误富信息法” 的工程化延伸，用于在 introspection 关闭时仍能安全地观察错误面和 schema 影子线索。
