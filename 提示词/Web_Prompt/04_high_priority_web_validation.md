# 04 高优先级 Web 验证方向

请优先验证以下方向，不要平均用力。

1. 登录前后页面入口差异。
2. 低权限用户直接访问高权限页面。
3. 普通用户直接访问管理页面。
4. 前端隐藏按钮对应的后端请求是否仍可访问。
5. 前端路由守卫与后端权限是否一致。
6. 页面参数、URL 参数、hash、query 是否影响对象选择。
7. tenant_id、org_id、workspace_id、project_id 是否可通过页面或请求变体影响数据边界。
8. user_id、owner_id、role_id、status、permission、scope 是否可由前端传入并影响结果。
9. 列表页、详情页、搜索页、报表页之间权限是否一致。
10. preview、export、download、print 是否和主页面权限一致。
11. 搜索、自动补全、报表是否比详情页返回更多数据。
12. 上传、预览、下载是否存在对象归属校验不一致。
13. 导出任务结果是否绑定创建者、角色和租户。
14. 下载链接是否可被其他用户复用。
15. redirect_url、callback_url、return_url、next 参数边界是否一致。
16. invite、reset、verify、magic link 页面是否正确绑定用户、租户、对象和有效期。
17. Cookie 属性是否满足预期会话边界。
18. session 是否和用户、角色、租户正确绑定。
19. 退出登录后旧页面、旧请求、旧缓存是否仍可访问敏感内容。
20. CSRF 保护是否覆盖状态变更请求。
21. CORS 是否符合预期来源边界。
22. CSP 是否能限制非预期脚本来源。
23. localStorage / sessionStorage / IndexedDB 是否保存敏感字段。
24. 前端存储中的 role、tenant、permission、scope 是否影响后端请求。
25. service worker 是否缓存认证响应或敏感数据。
26. 浏览器后退缓存是否显示退出后的敏感页面。
27. 页面缓存是否跨用户或跨租户复用。
28. JS bundle 是否暴露隐藏 API、默认配置、测试开关、内部 endpoint。
29. sourcemap 是否可访问并暴露真实接口或内部路径。
30. 静态资源是否暴露配置、环境变量、日志、示例数据。
31. 错误页面是否暴露 stack、路径、SQL、token、内部接口或依赖信息。
32. health、metrics、debug、internal、legacy、example 页面是否默认可访问。
33. WebSocket 订阅后是否能接收非当前用户或非当前租户事件。
34. GraphQL 字段级权限是否和页面权限一致。
35. 重复点击、刷新、后退、并发提交是否造成状态不一致。
36. 多标签页切换用户、角色、租户后是否出现旧数据复用。
37. 浏览器自动填充、隐藏字段、禁用字段是否可影响提交内容。
38. Content-Type、重复参数、数组参数、嵌套参数是否影响后端处理。
39. 大小写、尾斜杠、双斜杠、编码路径是否影响页面和接口权限。
40. Windows 路径分隔符、文件名大小写是否影响上传、下载、预览或导出边界。

每个高优先级项必须按以下格式处理：

- hypothesis
- affected_page_url
- affected_network_request
- actor
- boundary
- browser_action
- modified_input
- expected_secure_result
- actual_result
- evidence
- conclusion
- classification

禁止只写“可能存在风险”。必须说明如何验证，以及验证结果。
