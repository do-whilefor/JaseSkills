# Basic Example：本地 Web 项目认证门禁验证

## 场景

用户提供一个本地 Node.js Web 项目：

```text
project_root: C:\work\demo-shop
base_url: http://127.0.0.1:3000
授权边界：仅本地仓库、本地服务、测试数据库、测试账号
允许创建 evidence/ 和 tests/security/
测试数据库：docker-compose.test.yml
```

## Claude 应执行的步骤

### 1. 范围确认

```markdown
scope.allowed = true
scope.reason = 目标是本机授权项目和本地服务
scope.local_targets = ["C:\\work\\demo-shop", "http://127.0.0.1:3000"]
scope.forbidden_targets = ["公网", "第三方真实系统", "生产数据库", "真实用户数据", "中间人攻击", "DoS"]
```

### 2. 将读取的文件清单

```markdown
| 类别 | 路径/模式 | 目的 | 预期输出 |
|---|---|---|---|
| 启动说明 | README.md | 找启动命令 | start_command |
| 依赖 | package.json | 识别 Express、session、JWT 依赖 | stack |
| 路由 | src/routes/** | 识别 HTTP 入口 | routes.json |
| 认证 | src/middleware/auth.js | 识别登录校验 | auth_surface_matrix.md |
| 模型 | prisma/schema.prisma | 识别 User、Role、Tenant、Session | test_accounts.json |
| 测试 | tests/**, seed/** | 找测试账号 | test_accounts.json |
```

### 3. 暴露面矩阵片段

```markdown
| 入口名称 | 文件路径 | 方法/事件 | 是否需要登录 | 需要的角色/权限/租户 | 代码中的校验位置 | 动态验证方式 | 预期允许账号 | 预期拒绝账号 | 风险假设 | 证据需求 |
|---|---|---|---|---|---|---|---|---|---|---|
| 订单详情 | src/routes/orders.js | GET /api/orders/:id | 是 | owner 或 admin，同租户 | requireAuth + orderOwnerCheck | supertest/curl | user_a,admin | anonymous,user_b,disabled_user | 查询可能缺 tenant scope | 状态码、响应 order_id/user_id/tenant_id、测试输出 |
```

### 4. 动态验证样本

正向样本：

```bash
curl -i -H "Authorization: Bearer <user_a_test_token>" http://127.0.0.1:3000/api/orders/order_a
```

预期：

```text
200，返回 order_a，owner=user_a，tenant=tenant_a
```

反向样本：

```bash
curl -i -H "Authorization: Bearer <user_a_test_token>" http://127.0.0.1:3000/api/orders/order_b
```

预期：

```text
401 / 403 / 404，不返回 user_b 或 tenant_b 私有字段
```

### 5. 结论处理

如果反向样本返回 200，但响应内容为空或只包含公共字段，不能直接写 confirmed。必须继续确认：

```text
是否返回 user_b 私有字段
是否产生跨租户效果
是否写入或改变数据库
是否有服务端日志证据
是否有可复现测试用例
```

证据不足时写入：

```text
结论等级：candidate
不能确认为 confirmed 的原因：仅状态码异常，不足以证明越权效果
最小动态复现实验：补充响应字段对比和 DB/log 检查
```

## 最小输出

```text
evidence/run-manifest.json
evidence/routes.json
evidence/auth_surface_matrix.md
evidence/test_accounts.json
evidence/replay_results.json
evidence/findings.md
```

## 不允许输出

```markdown
## confirmed
- 订单接口可能存在越权，因为代码里没看到权限判断。
```

原因：没有动态请求证据、没有正反对照、没有异常成功结果。
