# 完整示例：REST + 文件 + GraphQL + WebSocket + 异步任务

## 输入

```text
项目路径：C:\work\local-collab-app
授权范围：仅限本机项目、本地 PostgreSQL、本地 MinIO、本地测试账号和测试租户。
本地 base URL：http://127.0.0.1:8080
```

## 测试身份

| 账号标识 | 角色 | 租户 | 状态 |
|---|---|---|---|
| anonymous | 未登录 | 无 | 未登录 |
| user_a | 普通用户 | tenant_a | 启用 |
| user_b | 普通用户 | tenant_b | 启用 |
| manager_a | 租户管理员 | tenant_a | 启用 |
| manager_b | 租户管理员 | tenant_b | 启用 |
| admin | 系统管理员 | 全局 | 启用 |
| disabled_user | 普通用户 | tenant_a | 禁用 |
| readonly_user | 只读用户 | tenant_a | 启用 |
| unverified_user | 普通用户 | tenant_a | 未验证 |
| role_changed_user | 原 manager 后降权 | tenant_a | 已降权 |

## 测试资源

| 资源标识 | 类型 | 所属用户 | 所属租户 | 状态 |
|---|---|---|---|---|
| tenant_a_private_resource | project | user_a | tenant_a | active |
| tenant_b_private_resource | project | user_b | tenant_b | active |
| tenant_a_file | file | user_a | tenant_a | active |
| tenant_b_file | file | user_b | tenant_b | active |
| tenant_a_export_job | export_job | user_a | tenant_a | completed |
| tenant_b_export_job | export_job | user_b | tenant_b | completed |
| draft_resource | document | user_a | tenant_a | draft |
| archived_resource | document | user_a | tenant_a | archived |
| deleted_resource | document | user_a | tenant_a | deleted |

## 暴露面矩阵摘录

| 入口名称 | 请求方法或事件名 | 路径 / resolver / handler | 代码文件 | 资源类型 | 资源归属字段 | 预期访问角色 | 预期禁止角色 | 预期租户边界 | 权限校验位置 | 可能缺失的校验点 | 动态验证方法 | 正向样本 | 反向样本 | 证据需求 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| project detail | GET | `/api/projects/:id` | `src/controllers/project.ts` | project | `tenant_id` | tenant member | non-member | tenant_id | `requireAuth` | tenant scope | curl | user_a -> tenant_a project | user_a -> tenant_b project | curl + response | candidate |
| file preview | GET | `/files/:id/preview` | `src/controllers/file.ts` | file | `tenant_id`, `owner_id` | owner, tenant manager | other tenant | tenant_id | unknown | preview 二次校验 | curl | user_a -> tenant_a_file | user_a -> tenant_b_file | curl + screenshot | candidate |
| GraphQL project | query | `project(id)` resolver | `src/graphql/project.resolver.ts` | project | `tenant_id` | tenant member | other tenant | tenant_id | resolver guard unknown | nested resolver scope | GraphQL request | user_a -> tenant_a project | user_a -> tenant_b project | request + response | candidate |
| WS room subscribe | subscribe | `joinRoom` | `src/ws/rooms.ts` | room | `tenant_id` | tenant member | other tenant | tenant_id | connect auth | message-level tenant check | WS client | user_a -> tenant_a room | user_a -> tenant_b room | trace | candidate |
| export download | GET | `/api/exports/:jobId/download` | `src/controllers/export.ts` | export_job | `tenant_id`, `created_by` | job owner, tenant manager | other tenant | tenant_id | create job only | download 二次校验 | curl | user_a -> own export | user_a -> tenant_b export | curl + file hash | candidate |

## confirmed 写法示例

### AUTHZ-20260607-001：导出结果下载缺少下载者租户校验

| 字段 | 内容 |
|---|---|
| 漏洞标题 | 导出结果下载缺少下载者租户校验 |
| 类型 | 文件越权 / 多租户越权 |
| 影响接口 | `GET /api/exports/:jobId/download` |
| 影响文件 | `src/controllers/export.ts` |
| 影响角色 | tenant_a 普通用户可下载 tenant_b 导出结果 |
| 影响租户 | tenant_a、tenant_b |
| 影响资源 | tenant_b_export_job |
| 触发条件 | 获取或猜测 jobId 后，以其他租户用户请求下载接口 |
| 正向请求 | user_b 下载 tenant_b_export_job 成功 |
| 反向请求 | user_a 下载 tenant_b_export_job 异常成功 |
| 实际异常成功结果 | 返回 200 和 tenant_b 导出 CSV 内容 |
| 状态码 | 200 |
| 响应关键字段 | CSV 中出现 `tenant_id=tenant_b` |
| 数据库或日志证据 | `evidence/logs/AUTHZ-20260607-001.log` |
| HAR / trace / screenshot / curl / test output 路径 | `evidence/curl/AUTHZ-20260607-001.txt` |
| 可复现步骤 | 1. 登录 user_b 创建导出任务；2. 登录 user_a 请求同一 jobId 下载；3. 观察返回 tenant_b CSV |
| 最小修复建议 | 下载接口按 jobId 查询后校验当前用户 tenant_id 与 job.tenant_id，并校验当前角色是否允许下载 |
| 修复后的回归测试 | `evidence/tests/export-download-authz.spec.ts` |
| 严重性判断 | 高：跨租户文件数据泄露 |
| 结论等级 | confirmed |

## candidate 写法示例

| 字段 | 内容 |
|---|---|
| 入口 | `query project(id) { members { email } }` |
| 可疑代码文件 | `src/graphql/member.resolver.ts` |
| 可疑点 | parent project resolver 有 tenant 校验，members nested resolver 直接按 projectId 查询 |
| 缺失的动态证据 | 尚未发出 user_a 查询 tenant_b project members 的 GraphQL 请求 |
| 最小动态复现计划 | 创建 tenant_a/tenant_b 项目和成员，以 user_a token 请求 tenant_b project 的 members 字段 |
| 当前结论 | candidate |

## false_positive 写法示例

| 字段 | 内容 |
|---|---|
| 怀疑点 | `joinRoom` 消息由客户端提交 roomId |
| 动态请求 | user_a 连接后发送 tenant_b roomId |
| 拒绝结果 | 服务端返回 `forbidden_room` 并断开订阅 |
| 排除依据 | message 层重新查询 room.tenant_id 并与 session tenant_id 对比 |
| 证据文件 | `evidence/traces/AUTHZ-20260607-003.ws-trace.json` |
| 结论 | false_positive |

## blocked 写法示例

| 编号 | 阻塞对象 | 阻塞原因 | 缺少什么 | 本地补齐方法 | 影响范围 | 当前结论 |
|---|---|---|---|---|---|---|
| B-001 | OAuth bind state | 项目未配置本地 OAuth provider | 本地 OAuth mock provider、回调 URL、测试 client id | 使用项目测试框架添加 mock OAuth provider，不触达真实第三方 | UC-47 | blocked |
