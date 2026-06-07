# Basic Example

## 输入

```text
使用 local-injection-verify。
项目路径：D:\lab\demo-shop
本地地址：http://127.0.0.1:3000
启动命令：npm run dev
测试数据库：demo_shop_test，可用 npm run db:reset 回滚
测试账号：user_a@local.test 普通用户 tenant-a；admin_a@local.test 低权限管理员 tenant-a；admin_b@local.test 低权限管理员 tenant-b
日志位置：D:\lab\demo-shop\logs\app.log
测试目录：D:\lab\demo-shop\tmp\security-marker
任务触发：npm run worker:test
目标：输出注入暴露面矩阵、动态验证计划和反查修正版报告。没有动态证据不得 confirmed。
```

## 合格输出片段

```markdown
## 0. 授权与安全边界确认
- 授权范围：本地 demo-shop 测试项目。
- 测试数据库：demo_shop_test，可通过 npm run db:reset 回滚。
- 禁止行为确认：未访问公网敏感目标；未执行破坏性命令；未读取真实敏感数据。

## 2. 注入暴露面矩阵
| 编号 | 输入入口 | 参数名 | 参数类型 | 角色/租户要求 | 代码路径 | sink 类型 | 解释器/组件 | 过滤/转义/参数化情况 | 动态验证方式 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| INJ-EXP-001 | HTTP query | sort | string | 普通用户/tenant-a | routes/products -> services/search | search DSL | 本地搜索组件 | allowlist 未确认 | marker 字段对照，采集响应和日志 | candidate |

## 3. 动态验证计划
### PLAN-INJ-001：搜索排序字段边界
- 对应矩阵编号：INJ-EXP-001
- 目标：验证 sort 参数是否只接受 allowlist 字段。
- 正向请求/触发步骤：使用已知安全字段触发搜索。
- 负向对照：使用不在 allowlist 的 marker 字段。
- marker：INJ_MARKER_20260607T153000Z_A1B2C3
- 预期安全行为：请求被拒绝，或按默认排序处理，日志不显示 marker 进入查询 DSL。
- 异常行为判定：日志或响应显示 marker 进入搜索 DSL 字段位置。
- 证据采集位置：HTTP 请求/响应、app.log、搜索组件调试日志。
- 回滚方式：无状态改变；若产生搜索历史，通过测试数据库重置清理。
- 风险控制：不使用高成本查询，不触发长时间执行。
```

## 不合格输出

```markdown
发现高危注入漏洞，建议修复。
```

不合格原因：没有画像、矩阵编号、marker、动态请求、负向对照、证据位置、回滚方式，不能称为 confirmed。
