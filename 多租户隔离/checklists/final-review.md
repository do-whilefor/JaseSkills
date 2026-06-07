# Final Review

用于交付前反向审判。目标是把缺证据的 confirmed 降级，把漏测入口转成下一步最小动态验证请求。

## 1. Skill 文件审查

- [ ] 是否重新读取 TXT 和全部 Skill 文件。
- [ ] 是否只保留 1 个主 Skill。
- [ ] 是否存在空壳目录或文件。
- [ ] 是否存在重复文件。
- [ ] 命名是否为小写英文短横线。
- [ ] 命名是否能看出租户隔离动态验证主题。
- [ ] `SKILL.md` 是否含适用范围、不适用范围、输入、输出、原文复刻、工程化补强、核心工作流、阶段步骤、质量门禁、幻觉控制、失败处理、输出格式、自检、映射表。
- [ ] `templates/output-template.md` 是否有可填写字段。
- [ ] `checklists/quality-gate.md` 是否能验收 TXT 复刻和动态验证。
- [ ] `examples/` 是否贴近本地授权租户隔离主题。
- [ ] `tests/` 是否能发现漏复刻、摘要化、无关扩展、命名失败、目录臃肿、缺输入输出、缺门禁、缺失败处理、缺映射、补强伪装原文。

## 2. confirmed 逐条反查模板

```markdown
### <漏洞编号>

- [ ] 攻击账号属于租户 A。证据：
- [ ] 目标资源属于租户 B。证据：
- [ ] A 对 B 资源没有合法授权。证据：
- [ ] 有正向样本。证据：
- [ ] 有反向样本。证据：
- [ ] 有角色对照。证据：
- [ ] 有租户对照。证据：
- [ ] 有请求和响应证据。证据：
- [ ] 已排除公开资源、共享资源、管理员预期权限。证据：
- [ ] 已验证同资源 list/detail/search/export/update/import/file/websocket/graphql 路线。证据：
- [ ] 任一项缺失时已降级 candidate。降级原因与补证计划：
```

## 3. candidate 逐条反查模板

```markdown
### <候选编号>

- [ ] 未 confirmed 原因：
- [ ] 缺少账号：
- [ ] 缺少租户：
- [ ] 缺少 marker：
- [ ] 缺少动态请求：
- [ ] 最小确认请求：
- [ ] 什么响应代表 confirmed：
- [ ] 什么响应代表 blocked：
- [ ] 其他可绕过入口：
- [ ] 是否可通过隐藏参数、GraphQL、WebSocket、导出、搜索、后台任务继续验证：
```

## 4. 30 个覆盖盲区

每项必须写已覆盖、未覆盖或不适用，并写证据、原因、下一条最小动态验证请求。

- [ ] 1. 前端 JS 中存在但 UI 没暴露的 API。
- [ ] 2. sourcemap 还原出的历史接口。
- [ ] 3. deprecated API、v1/v2/v3 老接口。
- [ ] 4. 移动端 API、内部 API、admin API。
- [ ] 5. GraphQL node/globalId/nested resolver。
- [ ] 6. WebSocket/SSE/channel/room 订阅。
- [ ] 7. 搜索、报表、导出、审计日志、通知中心。
- [ ] 8. 文件预览、缩略图、临时文件、预签名 URL。
- [ ] 9. Webhook 配置、Webhook 日志、Webhook 重放。
- [ ] 10. API Key、Service Token、Integration Token。
- [ ] 11. OAuth/SAML/SSO 绑定租户混淆。
- [ ] 12. 邀请链接、成员移除、角色降级后的旧 session。
- [ ] 13. 当前租户切换后的 session/context 污染。
- [ ] 14. cache key 未带 tenant。
- [ ] 15. background job 丢失 tenant context。
- [ ] 16. idempotency key 跨租户复用。
- [ ] 17. queue/job/export_id/import_id 跨租户读取。
- [ ] 18. soft delete/archive/trash 绕过租户过滤。
- [ ] 19. count/sum/report 聚合数据泄露。
- [ ] 20. ORM preload/include/populate 加载跨租户子对象。
- [ ] 21. Raw SQL 漏 tenant_id。
- [ ] 22. 只过滤父对象，不过滤子对象。
- [ ] 23. 只过滤 list，不过滤 detail。
- [ ] 24. 只过滤 detail，不过滤 export。
- [ ] 25. 只过滤 UI，不过滤 API。
- [ ] 26. 只过滤 REST，不过滤 GraphQL。
- [ ] 27. 只过滤 HTTP，不过滤异步任务。
- [ ] 28. 只校验 user_id，不校验 tenant_id。
- [ ] 29. 只校验 role，不校验资源归属。
- [ ] 30. 信任客户端传入 tenant_id/org_id/workspace_id。

## 5. 15 类偏门思路

- [ ] 父子资源错配：A parent + B child；B parent + A child。
- [ ] 创建时归属污染：A 创建时注入 B tenant/org/workspace。
- [ ] 更新时归属迁移：A 更新自己资源时注入 B tenant。
- [ ] 查询时过滤污染：include_all/include_archived/tenant/org/workspace/scope=all。
- [ ] 导出任务错租户：B export 后 A 查 export_id/download_url/job_id/task_id。
- [ ] 缓存串租户：A/B 交替请求相同 URL、object id、search query。
- [ ] 后台任务丢上下文：worker 是否全局查询或不重新查权限。
- [ ] WebSocket 频道可猜：A 订阅 B tenant/project/notification channel。
- [ ] GraphQL nested 绕过：顶层校验后嵌套拉 B 子对象。
- [ ] 多租户切换污染：切换当前租户后重放旧请求。
- [ ] 成员移除后残留访问：旧 token/session/API key。
- [ ] 只读角色写入：viewer 通过隐藏 API、批量、导入、mutation、event 写入。
- [ ] 平台管理员能力泄露：tenant admin 调平台接口或 impersonation。
- [ ] 审计日志反向泄露：audit/activity/notification/history/version diff 泄露 B marker。
- [ ] 对象存储路径绕过：文件 ID、缩略图、预览、下载、导出鉴权链路不一致。

## 6. 第二轮结论

- [ ] 第一轮误报：
- [ ] 第一轮漏测：
- [ ] 第一轮证据不足：
- [ ] 第一轮未覆盖高危入口：
- [ ] 第二轮新增 confirmed：
- [ ] 第二轮新增 candidate：
- [ ] 仍未覆盖但风险很高的区域：
- [ ] 下一步最小动态验证清单：
- [ ] 优先修复项：
- [ ] 回归测试位置：
- [ ] 可信度评级 A/B/C/D：
- [ ] 非 A 差距：
