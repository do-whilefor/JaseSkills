# 质量门禁 Checklist

## A. 运行边界

- [ ] 已确认目标是本地授权测试环境。
- [ ] `local_base_url` 不是公网第三方资产。
- [ ] 已确认不读取真实用户隐私数据。
- [ ] 已确认不破坏数据库、不删除业务数据。
- [ ] 已确认写操作、删除、状态变更有回滚方式。
- [ ] 已确认所有验证只使用测试账号、测试租户、测试资源、marker 内容。
- [ ] 已确认 `evidence_dir` 可写。

## B. 暴露面建模

- [ ] 已枚举后端路由、API endpoint、GraphQL resolver、WebSocket、RPC、后台接口、文件下载、导出、预览、Webhook、回调接口。
- [ ] 已枚举前端 JS、隐藏 API、未在 UI 展示的参数、注释路径、source map、懒加载 chunk、移动端、管理端、内部端入口。
- [ ] 已枚举数据库模型：用户、组织、团队、租户、项目、订单、文件、消息、审批、邀请、token、session、绑定关系、共享关系。
- [ ] 已枚举权限代码：auth middleware、policy、guard、decorator、scope、tenant filter、owner check、serializer、repository、ORM query、service 层校验。
- [ ] 已枚举对象引用参数：id、uuid、slug、key、path、filename、user_id、org_id、tenant_id、team_id、project_id、order_id、file_id、message_id、workspace_id、account_id、resource_id、parent_id、owner_id、created_by、assignee_id、email、phone、username。
- [ ] 已检查框架默认行为：路由绑定、ORM 自动查询、序列化、批量更新、参数合并、JSON body 覆盖 query、multipart 参数解析、method override、GraphQL alias/batching、WebSocket room join、缓存 key。
- [ ] 暴露面矩阵包含 TXT 要求的 12 个字段，并为每个入口写证据路径。

## C. 测试环境

- [ ] 已确认 `user_a` 属于 `tenant_a`。
- [ ] 已确认 `user_b` 属于 `tenant_b`。
- [ ] 已确认 `manager_a` 是 `tenant_a` 管理角色。
- [ ] 已确认 `admin_local` 仅用于本地测试环境准备和归属证明。
- [ ] 已确认 `anonymous` 为未登录状态。
- [ ] tenant_a 下每类关键资源至少 2 个。
- [ ] tenant_b 下每类关键资源至少 2 个。
- [ ] 每类关键资源记录 owner_id、tenant_id、org_id、visibility、status、marker。
- [ ] 每个被测资源都有归属证明。
- [ ] 每个修改类验证都有 before、after、rollback 证据。

## D. 动态验证

- [ ] 每个候选问题已执行正向验证，或写明 `not_run` 原因。
- [ ] 每个候选问题已执行反向验证，或写明 `not_run` 原因。
- [ ] 每个候选问题已执行越界尝试，或写明 `not_run` 原因。
- [ ] 修复后验证已执行，或修复状态标为 `unverified`。
- [ ] path 参数已测试或标记 `not_run`。
- [ ] query 参数已测试或标记 `not_run`。
- [ ] JSON body 已测试或标记 `not_run`。
- [ ] form-data 已测试或标记 `not_run`。
- [ ] header 已测试或标记 `not_run`。
- [ ] cookie 已测试或标记 `not_run`。
- [ ] GraphQL variable 已测试或标记 `not_run`。
- [ ] WebSocket payload 已测试或标记 `not_run`。

## E. 误报控制

- [ ] 没有把静态可疑写成 `confirmed`。
- [ ] 没有把 200 空响应写成 `confirmed`。
- [ ] 没有把前端隐藏按钮写成后端缺陷。
- [ ] 没有把报错差异写成越界成功。
- [ ] 没有把管理员设计允许访问写成漏洞。
- [ ] 没有把测试数据配置错误写成代码缺陷。
- [ ] 没有在缺少资源归属证明时写 `confirmed`。
- [ ] 没有在缺少请求、响应、账号、资源归属、数据库记录或日志证据时写 `confirmed`。

## F. 非常规路径

- [ ] 已检查旧接口、废弃接口、兼容接口、移动端接口、admin/internal 前缀接口，或记录 `not_run` / `blocked` 原因。
- [ ] 已检查前端未使用但后端仍注册的路由，或记录原因。
- [ ] 已检查自动生成 CRUD 路由，或记录原因。
- [ ] 已检查 REST 与 GraphQL 权限一致性，或记录原因。
- [ ] 已检查 API 直接请求是否绕过页面权限，或记录原因。
- [ ] 已检查列表与详情、导出、下载、统计接口过滤差异，或记录原因。
- [ ] 已检查更新接口是否接受 owner_id、tenant_id 等未暴露字段，或记录原因。
- [ ] 已检查批量接口是否逐项校验每一个 id，或记录原因。
- [ ] 已检查子资源、附件、评论、消息、历史版本权限，或记录原因。
- [ ] 已检查 include / expand / populate / preload 关联泄露，或记录原因。
- [ ] 已检查异步任务结果是否绑定用户或租户，或记录原因。
- [ ] 已检查 method override、content-type 切换、multipart、JSON merge patch，或记录原因。
- [ ] 已使用本地已知测试 UUID 验证对象引用；未做暴力枚举。
- [ ] 已检查缓存 key 是否包含 user/tenant scope，或记录原因。
- [ ] 已检查事务、状态机、审批、邀请、分享、绑定流程中间状态，或记录原因。

## G. 输出门禁

- [ ] 报告包含 `confirmed`、`blocked`、`candidate`、`false_positive` 四类结果。
- [ ] 每个 `confirmed` 包含 TXT 要求的全部字段。
- [ ] 报告包含反向审计 15 问逐条回答。
- [ ] 报告包含遗漏路径清单，且字段完整。
- [ ] 报告包含非常规路径补测结果，且每条有执行状态。
- [ ] 报告包含修复优先级。
- [ ] 报告包含本地回归测试脚本或脚本模板。
- [ ] 所有 `not_run`、`blocked`、`failed` 均写原因。
- [ ] Skill 保持 1 个主目录，无空壳文件，无无用目录。
- [ ] 原文复刻与工程化补强已分开标记。
