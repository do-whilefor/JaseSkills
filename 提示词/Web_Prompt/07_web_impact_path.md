# 07 Web 影响路径验证

不要只看单点问题。请尝试构造从 Web 页面入口到最终影响结果的路径。

impact_path 模板：

- path_id
- starting_page
- starting_actor
- frontend_action
- network_request
- step_1
- step_1_evidence
- step_2
- step_2_evidence
- step_3
- step_3_evidence
- final_impact
- affected_roles
- affected_tenants
- affected_objects
- required_conditions
- confirmed_steps
- likely_steps
- candidate_steps
- classification

优先寻找这些路径：

1. 普通页面 -> 隐藏参数 -> 对象归属变化 -> 读取他人数据。
2. 列表页 -> export 请求 -> 权限不一致 -> 批量读取数据。
3. 前端隐藏入口 -> network 请求可直接访问 -> 高权限操作。
4. webhook 配置页 -> 事件输入边界不完整 -> 后台状态变化。
5. 上传页 -> 文件处理差异 -> 本地 marker 证据。
6. GraphQL 请求 -> 字段级权限不一致 -> 跨租户数据暴露。
7. WebSocket 订阅 -> 租户隔离不完整 -> 接收越界事件。
8. 页面缓存 -> 角色或租户切换 -> 读取旧用户数据。
9. partial update 表单 -> status / role / tenant 变化 -> 权限边界变化。
10. reset / invite / verify 页面 -> token 绑定不足 -> 流程边界失效。
11. sourcemap -> 隐藏接口 -> 接口权限不一致 -> 数据访问。
12. debug / legacy 页面 -> 内部信息 -> 组合主流程缺陷。
13. 搜索建议 -> 对象存在性暴露 -> 详情请求组合验证。
14. 下载链接 -> 其他用户复用 -> 对象文件访问。
15. 导出任务 -> 结果文件未绑定创建者 -> 跨用户读取。

每条路径必须注明哪些步骤 confirmed，哪些步骤 likely，哪些步骤 candidate。
