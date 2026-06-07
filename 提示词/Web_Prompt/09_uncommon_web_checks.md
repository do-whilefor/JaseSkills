# 09 非常规 Web 验证角度

现在不要重复通用清单。请从 Web 页面行为、浏览器运行态、前端状态、请求差异、缓存行为、静态资源、权限边界和业务流程交叉点继续检查。

重点检查：

1. 前端路由守卫与后端权限是否不一致。
2. 前端隐藏入口是否对应可直接请求的接口。
3. disabled / readonly / hidden 字段是否可影响提交结果。
4. localStorage 中的 role、tenant、permission 是否影响请求。
5. sessionStorage 中的对象、租户、状态是否影响请求。
6. IndexedDB 是否保存敏感数据。
7. Cookie 是否缺少关键安全属性。
8. 退出登录后旧 Cookie、旧页面、旧缓存是否仍可读取敏感内容。
9. service worker 是否缓存认证响应。
10. 多标签页切换用户、角色、租户后是否复用旧状态。
11. 浏览器后退缓存是否显示退出后的敏感页面。
12. 页面级缓存是否跨用户或跨租户复用。
13. search / autocomplete / report 是否比详情页泄露更多数据。
14. preview / export / print / download 是否走不同权限路径。
15. 下载链接是否可被其他用户复用。
16. 导出任务结果是否绑定创建者和租户。
17. 附件、图片、缩略图、预览 URL 是否缺少对象权限校验。
18. redirect_url、callback_url、return_url、next 是否存在解析差异。
19. invite、reset、verify、magic link 是否绑定用户、租户、对象和有效期。
20. GraphQL resolver 是否绕过页面权限。
21. WebSocket 订阅后权限变化是否生效。
22. WebSocket 是否接收跨用户或跨租户事件。
23. JS bundle 是否暴露隐藏 API、测试开关、内部 endpoint。
24. sourcemap 是否暴露真实接口或内部路径。
25. manifest、robots、sitemap、well-known 是否暴露非预期入口。
26. health、metrics、debug、internal、legacy、example 是否默认可访问。
27. 错误提示是否暴露对象是否存在。
28. 错误页面是否暴露 stack、路径、SQL、token、内部接口。
29. 静态资源是否暴露配置、环境变量、日志、示例数据。
30. 重复点击是否造成重复状态变化。
31. 刷新、后退、重新提交是否造成状态不一致。
32. 并发提交是否影响额度、审批、库存、配额、邀请限制。
33. Content-Type 改变是否影响服务端解析。
34. 重复参数、数组参数、嵌套参数是否影响权限字段。
35. null、空字符串、空数组、空对象是否影响过滤器。
36. 大小写、尾斜杠、双斜杠、编码路径是否影响权限判断。
37. 文件名大小写是否影响上传、下载、预览。
38. Windows 路径反斜杠是否影响文件边界。
39. archive 内部路径是否影响解压或预览边界。
40. 临时文件、缓存文件、导出文件是否可被其他用户读取。

每项必须输出：

- 是否存在 Web 依据
- 相关页面 URL
- 相关 network 请求
- 相关参数
- 相关浏览器状态
- 验证方法
- 验证结果
- evidence
- classification
