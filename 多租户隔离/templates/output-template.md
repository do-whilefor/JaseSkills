# 项目租户隔离动态验证报告

## 0. 边界确认

| 项目 | 结果 |
|---|---|
| 目标项目路径 |  |
| API 基础地址 |  |
| 是否本地/本地容器/授权项目 |  |
| 是否使用测试数据库 |  |
| 是否只使用测试账号/测试租户/marker 数据 |  |
| 是否存在公网或第三方目标 |  |
| 是否存在 DoS/破坏性操作 |  |
| 写操作回滚方式 |  |
| 结论 | safe-scope / unsafe-scope / blocked |

## 1. 项目租户隔离事实画像

- 项目启动方式：
- 测试数据库位置：
- 认证入口：
- 租户模型：
- 租户识别来源：
- 关键授权中间件：
- 高风险模块：
- 高风险参数：
- 高风险表/模型：
- 高风险接口：
- 暂时无法确认的点：

### 1.1 来源证据

| 事实项 | 来源文件/接口/日志 | 证据摘要 | 状态 |
|---|---|---|---|
| 语言/框架/包管理器/入口 |  |  | confirmed/candidate/unknown |
| 路由系统 |  |  | confirmed/candidate/unknown |
| 认证系统 |  |  | confirmed/candidate/unknown |
| 授权系统 |  |  | confirmed/candidate/unknown |
| 租户模型与识别来源 |  |  | confirmed/candidate/unknown |
| 数据隔离方式 |  |  | confirmed/candidate/unknown |
| 前端暴露面 |  |  | confirmed/candidate/unknown |
| 非 HTTP 暴露面 |  |  | confirmed/candidate/unknown |

## 2. 暴露面总表

| 模块 | 文件路径 | 路由/接口 | 方法 | 参数 | 认证方式 | 租户来源 | 授权检查位置 | 风险点 | 动态验证状态 |
|---|---|---|---|---|---|---|---|---|---|
| IDOR/BOLA |  |  |  |  |  |  |  |  | not-started |
| 隐藏参数 |  |  |  |  |  |  |  |  | not-started |
| ORM/查询层 |  |  |  |  |  |  |  |  | not-started |
| GraphQL |  |  |  |  |  |  |  |  | not-applicable |
| WebSocket/SSE |  |  |  |  |  |  |  |  | not-applicable |
| 文件/导入导出 |  |  |  |  |  |  |  |  | not-started |
| 搜索/报表/审计/通知 |  |  |  |  |  |  |  |  | not-started |
| 邀请/成员/角色/切换 |  |  |  |  |  |  |  |  | not-started |
| API Key/Service Token/Integration |  |  |  |  |  |  |  |  | not-started |
| 缓存/队列/异步/批处理 |  |  |  |  |  |  |  |  | not-started |
| 管理后台/平台能力 |  |  |  |  |  |  |  |  | not-started |

## 3. 租户/角色/资源测试矩阵

### 3.1 角色矩阵

| 租户 | 角色/凭证 | 用户或 token 标识 | 身份证明方式 | 状态 | 缺口 |
|---|---|---|---|---|---|
| Tenant A | A_owner |  |  | ready/blocked |  |
| Tenant A | A_admin |  |  | ready/blocked |  |
| Tenant A | A_member |  |  | ready/blocked |  |
| Tenant A | A_viewer |  |  | ready/blocked |  |
| Tenant A | A_service_token |  |  | ready/blocked/not-applicable |  |
| Tenant B | B_owner |  |  | ready/blocked |  |
| Tenant B | B_admin |  |  | ready/blocked |  |
| Tenant B | B_member |  |  | ready/blocked |  |
| Tenant B | B_viewer |  |  | ready/blocked |  |
| Tenant B | B_service_token |  |  | ready/blocked/not-applicable |  |

### 3.2 marker 资源

| marker 名称 | 资源类型 | 资源 ID | 所属租户 | 创建账号 | 归属证明 | 回滚/清理方式 |
|---|---|---|---|---|---|---|
| TENANT_A_PRIVATE_DOC_MARKER | doc |  | A |  |  |  |
| TENANT_B_PRIVATE_DOC_MARKER | doc |  | B |  |  |  |
| TENANT_A_INVOICE_MARKER | invoice |  | A |  |  |  |
| TENANT_B_INVOICE_MARKER | invoice |  | B |  |  |  |
| TENANT_A_FILE_MARKER | file |  | A |  |  |  |
| TENANT_B_FILE_MARKER | file |  | B |  |  |  |
| TENANT_A_WEBHOOK_MARKER | webhook |  | A |  |  |  |
| TENANT_B_WEBHOOK_MARKER | webhook |  | B |  |  |  |
| TENANT_A_AUDIT_LOG_MARKER | audit_log |  | A |  |  |  |
| TENANT_B_AUDIT_LOG_MARKER | audit_log |  | B |  |  |  |

## 4. 动态验证执行记录

| 测试编号 | 候选编号 | 测试类型 | 执行账号 | 执行租户 | 目标资源 | 目标归属 | 请求摘要 | 响应摘要 | 状态 | 证据路径 | 结论依据 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T-001 | CAND-001 | 正向/反向/角色对照/租户对照 |  |  |  |  |  |  | not-started |  |  |

### 4.1 请求证据格式

```http
<方法> <本地路径>
Host: 127.0.0.1:<port>
Authorization: Bearer <redacted>
Cookie: session=<redacted>
Content-Type: application/json

{
  "marker": "...",
  "tenant_id": "...",
  "resource_id": "..."
}
```

### 4.2 响应证据格式

```json
{
  "status": 200,
  "marker": "TENANT_B_PRIVATE_DOC_MARKER",
  "tenant_id": "tenant_b",
  "resource_id": "doc_b_001"
}
```

## 5. confirmed 漏洞列表

| 漏洞编号 | 漏洞名称 | 严重等级 | 影响租户 | 影响角色 | 影响资源 | 状态 |
|---|---|---|---|---|---|---|
|  | 本轮未发现 |  |  |  |  |  |

## 6. high/critical 重点漏洞详情

### 【漏洞编号】

【漏洞名称】

【严重等级】

【影响租户】

【影响角色】

【影响资源】

【资源归属证明】

【请求身份证明】

【正向请求】

```http

```

【正向响应摘要】

```json

```

【越权请求】

```http

```

【越权响应摘要】

```json

```

【为什么这是租户隔离漏洞】

【为什么不是预期权限】

【复现步骤】

1. 
2. 
3. 

【最小化 PoC】

```bash

```

【涉及文件】

【根因代码】

```text

```

【修复建议】

【回归测试建议】

【证据文件路径：HAR / trace / screenshot / log，如有】

## 7. candidate 漏洞列表

### 【候选编号】

【候选名称】

【代码位置】

【怀疑原因】

【缺少什么动态证据】

【下一步验证请求】

```http

```

【需要的账号/租户/marker】

【预期成功结果】

【预期阻断结果】

【不能确认的原因】

## 8. 同族漏洞拓展结果

【同族拓展结果】

- 根因模式：
- 命中的文件：
- 命中的接口：
- 已动态验证 confirmed：
- 仍为 candidate：
- 下一步测试计划：

| 原漏洞 | 根因模式 | 同族文件 | 同族接口 | 动态验证请求 | 结果 | 严重性 | 证据 |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

## 9. 未覆盖区域和原因

| 区域 | 是否覆盖 | 未覆盖原因 | 风险 | 下一条最小动态验证请求 |
|---|---|---|---|---|
| IDOR/BOLA |  |  |  |  |
| 后端接受前端未暴露参数 |  |  |  |  |
| ORM/查询层租户过滤 |  |  |  |  |
| GraphQL |  |  |  |  |
| WebSocket/SSE |  |  |  |  |
| 文件/对象存储/附件/导入导出 |  |  |  |  |
| 搜索/报表/审计日志/通知 |  |  |  |  |
| 邀请/成员/角色/组织切换 |  |  |  |  |
| API Key/Service Token/Integration |  |  |  |  |
| 缓存/队列/异步任务/批处理 |  |  |  |  |
| 管理后台/平台管理员/支持人员 |  |  |  |  |

## 10. 修复建议

| 根因类型 | 修复动作 | 涉及文件/模块 | 优先级 | 验收方式 |
|---|---|---|---|---|
| 缺少 tenant filter | 统一在 repository/service/query scope 加当前租户 |  |  | A 访问 B marker 被阻断 |
| 信任客户端 tenant_id | 服务端从认证上下文取 tenant，不接受客户端覆盖 |  |  | 注入 B tenant 无效 |
| 文件鉴权不一致 | preview/thumbnail/download/export 统一资源归属校验 |  |  | A 不能读取 B 文件 marker |
| cache/job key 缺 tenant | cache/job/storage/idempotency key 加 tenant/user/scope |  |  | A/B 请求不串数据 |
| worker 丢上下文 | job payload 使用可信 tenant context，worker 重新查权限 |  |  | A 任务不处理 B 数据 |

## 11. 回归测试用例

| 用例编号 | 覆盖对象 | 账号 | 租户 | 资源 | 请求 | 预期结果 | 断言 |
|---|---|---|---|---|---|---|---|
| REG-001 | 跨租户读取阻断 | A_owner | A | B marker |  | 403/404/空数组 | 响应不含 `TENANT_B_*` |
| REG-002 | 角色对照 | A_viewer | A | A marker |  | 按角色规则阻断或只读 | viewer 不写入 |
| REG-003 | service token | A_service_token | A | B marker |  | 403/404 | token 不跨租户 |
| REG-004 | 导出 | A_owner | A | B export_id |  | 403/404 | 不能下载 B 导出 |
| REG-005 | 文件 | A_owner | A | B file_id |  | 403/404 | 不能预览/下载 B 文件 |

## 12. 本轮审计可靠性自我评估

评级：A / B / C / D

评级依据：

- A：核心入口、冷门入口、异步入口、文件入口、搜索导出、GraphQL/WebSocket 均已动态验证。
- B：核心 HTTP API 已动态验证，但部分异步/文件/实时入口未覆盖。
- C：主要还是静态审计，动态证据不足。
- D：结论不可信，需要重做。

| 非 A 差距 | 具体动态验证 | 所需账号/租户/marker | 阻塞原因 | 下一步 |
|---|---|---|---|---|
|  |  |  |  |  |

## 13. 第二轮反向审判复核结果

### 13.1 confirmed 逐条反查

| 漏洞编号 | A 身份 | B 归属 | A 无授权 | 正向 | 反向 | 角色对照 | 租户对照 | 请求响应 | 排除公开/共享/admin | 同资源多入口 | 结果 |
|---|---|---|---|---|---|---|---|---|---|---|---|
|  | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | yes/no | 保持 confirmed / 降级 candidate |

### 13.2 candidate 逐条反查

| 候选编号 | 未 confirmed 原因 | 缺账号 | 缺租户 | 缺 marker | 缺请求 | 最小确认请求 | confirmed 响应 | blocked 响应 | 其他入口 |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |

### 13.3 30 个覆盖盲区反查

| 序号 | 盲区 | 是否覆盖 | 证据在哪里 | 未覆盖原因 | 下一条最小动态验证请求 |
|---:|---|---|---|---|---|
| 1 | 前端 JS 中存在但 UI 没暴露的 API |  |  |  |  |
| 2 | sourcemap 还原出的历史接口 |  |  |  |  |
| 3 | deprecated API、v1/v2/v3 老接口 |  |  |  |  |
| 4 | 移动端 API、内部 API、admin API |  |  |  |  |
| 5 | GraphQL node/globalId/nested resolver |  |  |  |  |
| 6 | WebSocket/SSE/channel/room 订阅 |  |  |  |  |
| 7 | 搜索、报表、导出、审计日志、通知中心 |  |  |  |  |
| 8 | 文件预览、缩略图、临时文件、预签名 URL |  |  |  |  |
| 9 | Webhook 配置、Webhook 日志、Webhook 重放 |  |  |  |  |
| 10 | API Key、Service Token、Integration Token |  |  |  |  |
| 11 | OAuth/SAML/SSO 绑定租户混淆 |  |  |  |  |
| 12 | 邀请链接、成员移除、角色降级后的旧 session |  |  |  |  |
| 13 | 当前租户切换后的 session/context 污染 |  |  |  |  |
| 14 | cache key 未带 tenant |  |  |  |  |
| 15 | background job 丢失 tenant context |  |  |  |  |
| 16 | idempotency key 跨租户复用 |  |  |  |  |
| 17 | queue/job/export_id/import_id 跨租户读取 |  |  |  |  |
| 18 | soft delete/archive/trash 绕过租户过滤 |  |  |  |  |
| 19 | count/sum/report 聚合数据泄露 |  |  |  |  |
| 20 | ORM preload/include/populate 加载跨租户子对象 |  |  |  |  |
| 21 | Raw SQL 漏 tenant_id |  |  |  |  |
| 22 | 只过滤父对象，不过滤子对象 |  |  |  |  |
| 23 | 只过滤 list，不过滤 detail |  |  |  |  |
| 24 | 只过滤 detail，不过滤 export |  |  |  |  |
| 25 | 只过滤 UI，不过滤 API |  |  |  |  |
| 26 | 只过滤 REST，不过滤 GraphQL |  |  |  |  |
| 27 | 只过滤 HTTP，不过滤异步任务 |  |  |  |  |
| 28 | 只校验 user_id，不校验 tenant_id |  |  |  |  |
| 29 | 只校验 role，不校验资源归属 |  |  |  |  |
| 30 | 信任客户端传入 tenant_id/org_id/workspace_id |  |  |  |  |

### 13.4 15 类偏门思路拓展

| 序号 | 偏门思路 | 是否测试 | 动态验证请求 | 结果 | 证据 |
|---:|---|---|---|---|---|
| 1 | 父子资源错配 |  |  |  |  |
| 2 | 创建时归属污染 |  |  |  |  |
| 3 | 更新时归属迁移 |  |  |  |  |
| 4 | 查询时过滤污染 |  |  |  |  |
| 5 | 导出任务错租户 |  |  |  |  |
| 6 | 缓存串租户 |  |  |  |  |
| 7 | 后台任务丢上下文 |  |  |  |  |
| 8 | WebSocket 频道可猜 |  |  |  |  |
| 9 | GraphQL nested 绕过 |  |  |  |  |
| 10 | 多租户切换污染 |  |  |  |  |
| 11 | 成员移除后残留访问 |  |  |  |  |
| 12 | 只读角色写入 |  |  |  |  |
| 13 | 平台管理员能力泄露 |  |  |  |  |
| 14 | 审计日志反向泄露 |  |  |  |  |
| 15 | 对象存储路径绕过 |  |  |  |  |

### 13.5 第二轮结论

1. 第一轮误报了哪些：
2. 第一轮漏测了哪些：
3. 第一轮证据不足的有哪些：
4. 第一轮没有覆盖的高危入口有哪些：
5. 第二轮新增 confirmed 漏洞：
6. 第二轮新增 candidate 漏洞：
7. 仍未覆盖但风险很高的区域：
8. 下一步最小动态验证清单：
9. 必须优先修复：
10. 必须写回归测试：

## 14. 距离 A 级可信度的差距

| 差距项 | 当前证据 | 需要补充的动态验证 | 预期完成后评级影响 |
|---|---|---|---|
|  |  |  |  |
