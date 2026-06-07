# Full Example：完整本地认证门禁动态验证输出示例

## 0. 运行清单

| 字段 | 内容 |
|---|---|
| 项目名称 | demo-shop |
| project_root | C:\work\demo-shop |
| base_url | http://127.0.0.1:3000 |
| 授权边界 | 本地仓库、本地服务、测试数据库、测试账号 |
| start_command | npm run dev:test |
| test_db_setup | docker compose -f docker-compose.test.yml up -d db && npm run db:seed:test |
| evidence_dir | evidence/ |
| service_started | true |
| 写操作回滚方式 | 测试数据库重建 + seed 重放 |

## 1. 项目认证架构摘要

| 项 | 结论 | 证据路径 |
|---|---|---|
| 语言/框架 | Node.js + Express | evidence/run-manifest.json |
| 认证模块 | src/middleware/auth.js | evidence/auth_surface_matrix.md |
| 权限模块 | src/policies/orderPolicy.js | evidence/auth_surface_matrix.md |
| session/token | JWT + refresh token | evidence/routes.json |
| Tenant 模型 | prisma/schema.prisma 中存在 tenantId | evidence/model-notes.md |
| 文件接口 | /api/files/:id/download | evidence/routes.json |
| GraphQL | 不存在 | evidence/routes.json |
| WebSocket | 存在 /ws/notifications | evidence/routes.json |

## 2. 测试账号和角色矩阵

| 账号引用名 | 角色 | 租户 | 状态 | 资源样本 | 凭据保存方式 | 用途 |
|---|---|---|---|---|---|---|
| anonymous | 未登录 | 无 | 未登录 | 无 | 无 | 受保护入口反向测试 |
| user_a | user | tenant_a | active | order_a,file_a | evidence/redacted-headers/user_a.json | 正向和跨用户反向 |
| user_b | user | tenant_b | active | order_b,file_b | evidence/redacted-headers/user_b.json | 跨用户/跨租户反向 |
| manager_a | manager | tenant_a | active | order_a | evidence/redacted-headers/manager_a.json | 中权限测试 |
| admin | admin | system | active | all_test_resources | evidence/redacted-headers/admin.json | 管理接口正向 |
| disabled_user | user | tenant_a | disabled | order_disabled | evidence/redacted-headers/disabled_user.json | 禁用状态反向 |
| unverified_user | user | tenant_a | unverified | order_unverified | evidence/redacted-headers/unverified_user.json | 邮箱未验证反向 |
| expired_session_user | user | tenant_a | expired | order_expired | evidence/redacted-headers/expired_session_user.json | 会话过期反向 |

## 3. 暴露面矩阵片段

| 入口名称 | 文件路径 | 方法/事件 | 是否需要登录 | 需要的角色/权限/租户 | 代码中的校验位置 | 动态验证方式 | 预期允许账号 | 预期拒绝账号 | 风险假设 | 证据需求 |
|---|---|---|---|---|---|---|---|---|---|---|
| 订单详情 | src/routes/orders.js | GET /api/orders/:id | 是 | owner/admin + tenant scope | requireAuth + orderPolicy.canRead | supertest | user_a,admin | anonymous,user_b,disabled_user | 查询可能缺 tenant scope | 状态码、响应 order.tenantId、测试输出 |
| 文件下载 | src/routes/files.js | GET /api/files/:id/download | 是 | owner/admin + tenant scope | requireAuth | curl | user_a,admin | anonymous,user_b | download handler 可能未调用 fileOwnerCheck | 状态码、Content-Disposition、文件 hash |
| WebSocket 通知 | src/ws/notifications.js | subscribe room | 是 | room owner 或同租户 | handshake auth | ws client | user_a | anonymous,user_b | 连接校验后消息订阅可能未复验 tenant | ws transcript |

## 4. replay_results.json 片段

```json
[
  {
    "case_id": "AUTH-001-P",
    "entry": "GET /api/orders/:id",
    "account": "user_a",
    "tenant": "tenant_a",
    "sample_type": "positive",
    "request": {
      "method": "GET",
      "url": "http://127.0.0.1:3000/api/orders/order_a",
      "headers_ref": "evidence/redacted-headers/user_a.json",
      "body_ref": null
    },
    "expected": {
      "status": [200],
      "effect": "返回 user_a 的 order_a"
    },
    "actual": {
      "status": 200,
      "key_fields": {"order_id": "order_a", "owner": "user_a", "tenant": "tenant_a"},
      "effect": "matched_expected"
    },
    "evidence_files": ["evidence/api/AUTH-001-P.txt"],
    "verdict": "pass",
    "reason": "合法用户访问本资源成功"
  },
  {
    "case_id": "AUTH-001-N",
    "entry": "GET /api/orders/:id",
    "account": "user_a",
    "tenant": "tenant_a",
    "sample_type": "negative",
    "request": {
      "method": "GET",
      "url": "http://127.0.0.1:3000/api/orders/order_b",
      "headers_ref": "evidence/redacted-headers/user_a.json",
      "body_ref": null
    },
    "expected": {
      "status": [401, 403, 404],
      "effect": "不得返回 user_b 或 tenant_b 资源"
    },
    "actual": {
      "status": 200,
      "key_fields": {"order_id": "order_b", "owner": "user_b", "tenant": "tenant_b"},
      "effect": "cross_tenant_private_data_returned"
    },
    "evidence_files": ["evidence/api/AUTH-001-N.txt", "evidence/tests/security/order-auth.test.js"],
    "verdict": "confirmed",
    "reason": "反向样本异常成功且返回跨租户私有资源"
  }
]
```

## 5. confirmed 示例

```markdown
## AUTH-001：订单详情接口缺少租户范围校验

- 结论等级：confirmed
- 影响范围：普通用户可读取其他租户订单详情。
- 受影响接口/文件/函数：GET /api/orders/:id，src/routes/orders.js，getOrderById。
- 触发前置条件：攻击者持有 user_a 的有效测试 token，并知道 tenant_b 的测试订单 id。
- 测试账号和测试资源：user_a/tenant_a/order_a，user_b/tenant_b/order_b。
- 正向请求和预期成功结果：user_a 请求 order_a 返回 200，owner=user_a，tenant=tenant_a。
- 反向请求和实际异常成功结果：user_a 请求 order_b 返回 200，owner=user_b，tenant=tenant_b。
- HTTP 状态码：正向 200，反向 200。
- 响应关键字段：order_id=order_b，owner=user_b，tenant=tenant_b。
- 数据库变化或日志证据：只读请求，无 DB 写入；服务日志见 evidence/logs/AUTH-001.log。
- Playwright trace / HAR / 截图 / curl / 测试用例：evidence/tests/security/order-auth.test.js，evidence/api/AUTH-001-N.txt。
- 为什么这是认证/门禁缺陷，而不是测试误差：正向样本证明 user_a 凭据有效；反向样本使用同凭据访问 tenant_b 私有资源并返回敏感字段，预期应拒绝或隐藏。
- 最小修复建议：订单查询必须绑定当前 session 的 user_id 或 tenant_id；管理员路径单独走 admin policy。
- 修复后的 negative test：user_a 请求 order_b 必须返回 403 或 404，且不得包含 owner/tenant/order 字段。
- 严重性判断依据：跨租户私有订单读取。
- 跨用户/跨角色/跨租户/跨状态/跨认证方式：跨用户、跨租户。
```

## 6. candidate 降级示例

```markdown
## AUTH-CAND-004：文件下载接口 owner 校验待验证

- 结论等级：candidate
- 风险假设：src/routes/files.js 中 download handler 只调用 requireAuth，未调用 fileOwnerCheck。
- 受影响入口：GET /api/files/:id/download。
- 静态依据：路由链中未看到 file policy。
- 已执行验证：未执行，原因是测试文件 seed 缺失。
- 缺失证据：user_a 和 user_b 的私有文件 fixture、反向请求响应、文件 hash 对比。
- 不能确认为 confirmed 的原因：没有动态请求证据和正反对照。
- 最小动态复现实验：创建 file_a、file_b；user_a 下载 file_a 应成功；user_a 下载 file_b 应 403/404；记录状态码、Content-Disposition、文件 hash。
- 需要的测试账号/资源：user_a、user_b、file_a、file_b。
- 预期证据文件：evidence/api/AUTH-CAND-004.txt，evidence/tests/security/file-download-auth.test.js。
```

## 7. blocked 示例

```markdown
## AUTH-BLOCK-002：禁用账号测试被阻塞

- 阻塞原因：仓库中未找到 disabled_user seed，也未找到账号状态字段的 fixture 创建方式。
- 已查找位置：README.md、prisma/schema.prisma、tests/fixtures、seed。
- 缺失输入：禁用账号创建方式或账号状态字段含义。
- 本地补齐方式：在 tests/security/seed-auth-users.js 中基于 User.status 创建 disabled_user，使用测试 DB，不改业务逻辑。
- 补齐后第一条验证命令：node tests/security/seed-auth-users.js && npm run test:security -- disabled-user
- 当前允许结论：blocked
```

## 8. 小众路径专项片段

| 类别 | 测试入口 | 测试账号 | 正向样本 | 反向样本 | 请求构造 | 预期结果 | 实际结果 | 证据文件 | 结论等级 | 修复建议 |
|---|---|---|---|---|---|---|---|---|---|---|
| 方法差异 | /api/orders/:id | user_a | GET order_a | HEAD order_b | HEAD /api/orders/order_b | 401/403/404 或无敏感头 | 403 | evidence/api/method-head.txt | false_positive | 无 |
| 参数污染 | /api/orders/search | user_a | tenant_id=tenant_a | query tenant_id=tenant_a + body tenant_id=tenant_b | POST JSON + query | 后端只信 session tenant | 未执行 |  | blocked | 补齐搜索接口 seed |

## 9. 最终验收回答片段

1. 哪些认证门禁缺陷已经动态确认？
   - AUTH-001 订单详情跨租户读取，证据见 evidence/api/AUTH-001-N.txt 和 tests/security/order-auth.test.js。
2. 哪些只是候选，为什么还不能确认？
   - AUTH-CAND-004 文件下载 owner 校验待验证，缺 user_b 私有文件 fixture 和反向请求证据。
3. 哪些路径没有覆盖，原因是什么？
   - OAuth 绑定：项目未实现 OAuthAccount 模型和 OAuth 回调路由，记录为 not_applicable。
4. 是否真实启动了服务并执行了请求？
   - 是，启动命令和日志见 evidence/run-manifest.json。
5. 是否生成了可复跑测试？
   - 是，见 tests/security/order-auth.test.js。
6. 是否保留了 HAR、trace、截图、日志或测试输出？
   - 保留测试输出和服务日志；本例未使用 Playwright。
7. 是否把所有 confirmed 都配了修复建议和回归测试？
   - 是。
8. 如果明天换一个审计人员，只根据 evidence/ 目录，能否复现结论？
   - 能，evidence 中包含请求、响应、账号引用、测试脚本和运行命令。
```
