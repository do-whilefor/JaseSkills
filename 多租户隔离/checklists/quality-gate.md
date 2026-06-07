# Quality Gate

未通过项必须修复；无法修复时在报告中标记 blocked、写原因和下一条最小动态验证请求。

## 1. TXT 复刻工程门禁

- [ ] 已重新读取原始 TXT。
- [ ] 已重新读取当前 Skill 全部文件。
- [ ] 已检查目录结构和文件命名。
- [ ] 已建立 TXT 到 Skill 映射表。
- [ ] 已区分原文复刻和工程化补强。
- [ ] 未把工程化补强写成 TXT 原文。
- [ ] 未读取的文件已标记“未验证，不得宣称已通过”。
- [ ] Skill 数量为 1；如超过 1，已有不可合并理由。
- [ ] 无空壳目录。
- [ ] 无空壳文件。
- [ ] 文件命名可对应 TXT 核心主题。
- [ ] 输出可追溯 TXT。

## 2. 边界门禁

- [ ] 目标为本机、本地容器、本地测试数据库或授权项目。
- [ ] 未访问公网敏感地址。
- [ ] 未测试第三方真实系统。
- [ ] 未执行 DoS、DDoS、压力破坏、爆破。
- [ ] 未删除数据库、清空文件、破坏业务数据。
- [ ] 未使用 MITM。
- [ ] 写操作只作用于 marker 数据。
- [ ] 写操作可回滚或已 blocked。
- [ ] 用户额外限制已记录并执行。

## 3. 脱敏门禁

- [ ] 未输出真实 secret、token、cookie、密码、私钥。
- [ ] Authorization 已脱敏。
- [ ] Cookie 已脱敏。
- [ ] 响应体只保留证明字段。
- [ ] 没有输出真实敏感业务数据。

## 4. 事实画像门禁

- [ ] 已记录语言、框架、包管理器、入口文件。
- [ ] 已记录启动方式和测试数据库位置。
- [ ] 已记录 REST/GraphQL/RPC/WebSocket/admin/API/internal 路由。
- [ ] 已记录 Session/JWT/OAuth/API Key/Service Token/CLI Token/Webhook Token。
- [ ] 已记录 RBAC/ABAC/Policy/Middleware/Guard/Decorator/Interceptor/Hook。
- [ ] 已记录 tenant/org/workspace/team/project/account/company/site/space/environment 等租户模型。
- [ ] 已记录租户识别来源。
- [ ] 已记录数据隔离方式。
- [ ] 已记录前端暴露面。
- [ ] 已记录非 HTTP 暴露面。
- [ ] 无法确认项已写入“暂时无法确认”。

## 5. 租户矩阵与 marker 门禁

- [ ] 已创建或识别租户 A 和租户 B。
- [ ] 已记录 A_owner、A_admin、A_member、A_viewer。
- [ ] 已记录 B_owner、B_admin、B_member、B_viewer。
- [ ] 项目支持 service token 时已记录 A_service_token、B_service_token。
- [ ] 项目不支持 service token 时已标记 not-applicable。
- [ ] 已创建或识别 10 个 A/B marker。
- [ ] 每个 marker 有资源 ID、归属证明、回滚或清理方式。

## 6. 暴露面门禁

- [ ] 表格包含模块、文件路径、接口、方法、参数、认证方式、租户来源、授权检查位置、风险点、动态验证状态。
- [ ] 每行落到具体文件和接口。
- [ ] 没有只写“检查接口权限”的空泛行。
- [ ] 每个高风险接口有测试账号或 blocked 原因。

## 7. 动态验证门禁

- [ ] 每个 candidate 有正向测试或未执行原因。
- [ ] 每个 candidate 有反向测试或未执行原因。
- [ ] 每个 candidate 有角色对照或未执行原因。
- [ ] 每个 candidate 有租户对照或未执行原因。
- [ ] 可行时覆盖 GET/POST/PUT/PATCH/DELETE 的无害 marker 请求。
- [ ] 已测 API，不只测 UI。
- [ ] 已追前端隐藏入口，不只测 API。
- [ ] 已检查 GraphQL/WebSocket/导入导出/后台任务/缓存/文件，或写 not-applicable/blocked。
- [ ] 每条动态请求有请求摘要、响应摘要、状态、证据路径或证据缺失说明。

## 8. confirmed 门禁

- [ ] 请求身份属于租户 A。
- [ ] 目标资源明确属于租户 B。
- [ ] 响应返回 B 数据，或对 B marker 发生未授权状态改变。
- [ ] 有正向样本和反向样本。
- [ ] 有可复现请求和响应证据。
- [ ] 有资源归属证明。
- [ ] 已排除测试数据污染、管理员预期权限、公开资源、缓存误判。
- [ ] confirmed 描述没有“可能”“疑似”“应该”“看起来”。

## 9. candidate 门禁

- [ ] 缺动态证据的点均标记 candidate。
- [ ] candidate 有代码位置、怀疑原因、缺少证据、下一步请求、账号/租户/marker、预期成功、预期阻断、不能确认原因。
- [ ] 没有把 candidate 写成 confirmed。

## 10. 覆盖路线门禁

- [ ] IDOR/BOLA。
- [ ] 后端接受前端未暴露参数。
- [ ] ORM/查询层租户过滤。
- [ ] GraphQL，或 not-applicable/blocked。
- [ ] WebSocket/SSE，或 not-applicable/blocked。
- [ ] 文件、对象存储、附件、导入导出。
- [ ] 搜索、报表、审计日志、通知中心。
- [ ] 邀请、成员、角色、组织切换。
- [ ] API Key / Service Token / Integration。
- [ ] 缓存、队列、异步任务、批处理。
- [ ] 管理后台/平台管理员/支持人员能力。
- [ ] 未覆盖路线有原因和下一条最小动态验证请求。

## 11. 同族拓展门禁

- [ ] 每个 confirmed 已追踪同 controller/service/repository/DTO/schema/model。
- [ ] 每个 confirmed 已追踪 list/detail/update/delete/export/search/import。
- [ ] 每个 confirmed 已追踪 REST/GraphQL/WebSocket/后台任务/文件入口。
- [ ] 每个 confirmed 已追踪同授权缺失、客户端 tenant 信任、cache/job/storage key、前端隐藏参数。
- [ ] 已输出同族拓展矩阵。

## 12. 第二轮反向审判门禁

- [ ] 已逐条反查 confirmed；缺任一证据项已降级 candidate。
- [ ] 已逐条反查 candidate。
- [ ] 已检查 30 个覆盖盲区。
- [ ] 已检查 15 类偏门思路。
- [ ] 已输出第一轮误报、漏测、证据不足、未覆盖高危入口。
- [ ] 已输出第二轮新增 confirmed、candidate。
- [ ] 已输出下一步最小动态验证清单、优先修复项、回归测试位置。
- [ ] 已给 A/B/C/D 评级；非 A 已列差距。
