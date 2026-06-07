# 交付前追责反查清单

## A. confirmed 逐条反查

对每一个 confirmed 单独复制本清单。任何一项无法提供证据时，不得保留 confirmed。

- [ ] 是否真的启动了本地服务？证据：
- [ ] 是否真的创建或识别了不同角色账号？证据：
- [ ] 是否真的创建或识别了不同租户资源？证据：
- [ ] 是否真的用 user_a 请求了 user_b 的资源？证据：
- [ ] 是否真的用 tenant_a 请求了 tenant_b 的资源？证据：
- [ ] 是否真的用普通用户请求了管理员接口？证据：
- [ ] 是否真的有正向成功样本？证据：
- [ ] 是否真的有反向失败预期样本？证据：
- [ ] 是否真的出现了异常成功结果？证据：
- [ ] 是否记录了状态码、响应体、日志、数据库变化或测试输出？证据：
- [ ] 是否有 HAR、trace、截图、curl 或自动化测试？证据：
- [ ] 是否确认返回内容有敏感性或产生越权效果？证据：
- [ ] 是否排除“只是看到 200 就误判为越权”？证据：
- [ ] 是否排除“只是看到代码缺少 guard 就误判为 confirmed”？证据：
- [ ] 是否排除“把前端限制当成后端限制”？证据：
- [ ] 是否检查同资源的其他方法？证据：
- [ ] 是否检查批量接口？证据：
- [ ] 是否检查导出、下载、预览、附件？证据：
- [ ] 是否检查 GraphQL nested resolver；不存在时是否说明？证据：
- [ ] 是否检查 WebSocket room / channel；不存在时是否说明？证据：
- [ ] 是否检查异步任务和队列；不存在时是否说明？证据：
- [ ] 是否检查旧版本接口和 legacy route？证据：
- [ ] 是否检查软删除、归档、草稿、审批状态？证据：
- [ ] 是否检查降权后旧 session？证据：
- [ ] 是否检查多租户缓存和导出文件缓存？证据：

处理规则：

- [ ] 全部通过，保留 confirmed。
- [ ] 缺动态请求、正反样本、异常成功、证据文件或复现步骤之一，降级为 candidate，并写入 replay_plan.md。
- [ ] 环境、账号、资源或依赖导致无法验证，改为 blocked，并写入 blocked.md。
- [ ] 动态证明拒绝访问，改为 false_positive，并写入 false_positives.md。
- [ ] 影响不稳定或证据不足，改为 needs_review。

## B. 漏测反查

- [ ] REST list/detail/create/update/delete 已覆盖或 blocked。
- [ ] export/import/download/preview/share/copy/archive/restore 已覆盖或 blocked。
- [ ] GET/POST/PUT/PATCH/DELETE/HEAD/OPTIONS 方法差异已覆盖或 blocked。
- [ ] JSON/form-data/x-www-form-urlencoded/text/plain/空 body/重复 key/数组 key/嵌套对象已覆盖或 blocked。
- [ ] path/query/body/header/cookie/session 参数污染已覆盖或 blocked。
- [ ] user_id/account_id/member_id/tenant_id/org_id/team_id/role/permission/is_admin/owner_id 等客户端字段已覆盖或 blocked。
- [ ] ids/items/filters/where/include/expand/fields/select/sort/group 批量和查询参数已覆盖或 blocked。
- [ ] ORM findMany/findFirst/findUnique/raw query/include/join/populate/preload 已检查或 blocked。
- [ ] GraphQL query/mutation/nested resolver/alias/fragment/batch/node/id/connection edges 已覆盖或 blocked。
- [ ] WebSocket connect/message/room/channel/tenant/user_id/resource_id 已覆盖或 blocked。
- [ ] 文件原件/缩略图/预览图/转码文件/临时文件/导出文件/附件 URL/缓存副本已覆盖或 blocked。
- [ ] 导出/报表/队列/Webhook/定时任务已覆盖或 blocked。
- [ ] 草稿/待审批/已审批/已拒绝/已取消/已删除/已归档/已过期已覆盖或 blocked。
- [ ] 升权/降权/移出组织/禁用/退出租户后的旧 session/token/cache 已覆盖或 blocked。
- [ ] Web/REST/GraphQL/WebSocket/移动端/后台/worker/CLI/Webhook 多入口差异已覆盖或 blocked。
- [ ] /v1、/legacy、/compat、/old、/admin-old、deprecated route 已覆盖或 blocked。
- [ ] catch-all、通配符、尾斜杠、大小写、URL 编码、重复斜杠、后缀格式、locale 前缀已覆盖或 blocked。
- [ ] 框架默认 allow、trust header、debug user、mock auth 已覆盖或 blocked。
- [ ] 前端隐藏按钮、隐藏菜单、隐藏参数、禁用按钮均已通过后端重放验证或 blocked。

## C. 文件交付反查

- [ ] `evidence/authz_surface_matrix.md` 存在且字段完整。
- [ ] `evidence/test_accounts.json` 存在或 blocked 说明完整。
- [ ] `evidence/test_resources.json` 存在或 blocked 说明完整。
- [ ] `evidence/replay_plan.md` 包含所有 candidate 最小复现计划。
- [ ] `evidence/replay_results.json` 包含动态请求结果。
- [ ] `evidence/findings.md` 只包含 confirmed。
- [ ] `evidence/false_positives.md` 包含排除依据。
- [ ] `evidence/blocked.md` 包含补齐办法。
- [ ] `evidence/curl/`、`evidence/tests/`、`evidence/logs/` 包含必要证据或 blocked 说明。

## D. 反幻觉反查

- [ ] 未把工程化补强写成 TXT 原文。
- [ ] 未把未读取文件写成已读取。
- [ ] 未把候选结构写成最终结构。
- [ ] 未用目录数量掩盖内容不足。
- [ ] 未用示例结论替代目标项目动态证据。
- [ ] 未保留没有调用价值的文件。
