# Full Example

本示例展示动态验证和反向审判如何合并为同一条证据链。项目、路径、账号、marker 均为虚构本地测试数据。

## 输入

```text
使用 local-injection-verify。
项目路径：D:\lab\ticket-lite
本地服务：http://127.0.0.1:8080
启动命令：docker compose -f docker-compose.test.yml up
测试数据库：ticket_lite_test，回滚方式 docker compose down -v 后重新 seed
测试账号：user-a 普通用户 tenant-a；reviewer-a 低权限管理员 tenant-a；user-b 普通用户 tenant-b
日志：D:\lab\ticket-lite\var\logs\app.log
测试目录：D:\lab\ticket-lite\var\tmp\marker
队列触发：php bin/console messenger:consume async --limit=1
目标：覆盖 HTTP、模板预览、导出、队列 worker、隐藏参数和二阶路径。没有动态证据不得 confirmed。
```

## 合格输出片段

```markdown
## 1. 项目运行画像
| 项目 | 结果 | 证据来源 | 状态 |
|---|---|---|---|
| 语言 | PHP | composer.json | 已识别 |
| 框架 | Symfony | composer.json, config/routes.yaml | 已识别 |
| 数据库 | PostgreSQL 测试库 | .env.test | 已识别 |
| ORM | Doctrine | composer.json, src/Repository | 已识别 |
| 模板引擎 | Twig | composer.json, templates/ | 已识别 |
| 队列/任务 | Symfony Messenger | config/packages/messenger.yaml | 已识别 |
| GraphQL/WebSocket/RPC | 未发现 | 未发现相关依赖和路由 | 未发现 |

## 2. 注入暴露面矩阵
| 编号 | 输入入口 | 参数名 | 参数类型 | 角色/租户要求 | 代码路径 | sink 类型 | 解释器/组件 | 过滤/转义/参数化情况 | 动态验证方式 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|---|
| INJ-EXP-001 | HTTP body | ticket.note | string | 普通用户 tenant-a | TicketController -> TicketService -> Doctrine entity -> AdminPreviewController | template render | Twig 预览 | 写入点有长度校验，触发点转义未确认 | 普通用户写入 marker，管理员预览，采集响应和日志 | candidate |
| INJ-EXP-002 | HTTP query | sort | string | 普通用户 tenant-a | TicketController -> TicketRepository | ORM order | Doctrine query builder | 字段 allowlist 已发现 | 安全字段 + marker 字段负向对照 | false positive |

## 4. 动态验证结果
### RESULT-INJ-001：工单备注二阶模板边界
- 对应计划：PLAN-INJ-001
- 状态：candidate
- 复现步骤：已完成普通用户写入；管理员预览需人工点击。
- 请求摘要：普通用户提交含 marker 的备注。
- 响应摘要：创建成功，返回测试对象 ID。
- 日志证据：写入日志存在；管理员预览日志未采集。
- 数据库/文件/任务证据：测试库中存在 marker 备注。
- 负向对照结果：普通备注写入成功。
- marker 是否被解释器处理：未验证。
- 严重性：undetermined。
- 为什么不是误报：仅证明可写入和可存储，未证明模板解释。
- 缺失证据：管理员预览响应、模板日志、负向预览对照。
- 修复建议：管理员预览和通知模板输出用户字段时统一转义；禁止把用户字段拼入模板源码。
- 回归测试建议：创建含 marker 的备注，管理员预览断言 marker 按文本展示且模板日志不出现表达式执行。

### RESULT-INJ-002：排序字段边界
- 状态：false positive
- 日志证据：allowlist 在 ORM query builder 前拦截 marker 字段。
- marker 是否被解释器处理：否。
- 为什么不是误报：marker 未进入查询构造。
- 回归测试建议：传入不存在字段时断言 400 或默认排序。

## 12.1 被降级的结论列表
| 原结论编号 | 原状态 | 新状态 | 降级原因 | 缺失证据 |
|---|---|---|---|---|
| RESULT-INJ-001 | confirmed | candidate | 未采集管理员预览响应和模板日志，不能证明 marker 被模板解释器处理 | 解释器处理证据、负向预览对照 |
```

## 关键验收点

- 存储型 marker 不等于 confirmed。
- 缺少解释器处理证据时降级为 candidate。
- 二阶链路必须保留写入点、存储位置、触发点和 sink。
- 下一步必须是最小安全验证步骤，而不是空泛描述。
