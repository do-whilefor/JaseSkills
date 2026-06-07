# 01 Web 事实基线

先不要直接输出问题。请先建立 web_surface_facts。

你必须通过浏览器访问和 network 观察，输出以下内容：

1. Web base URL。
2. 首页。
3. 登录入口。
4. 注册入口。
5. 重置密码入口。
6. 退出登录入口。
7. 普通用户入口。
8. 管理入口。
9. 公开页面。
10. 需要认证页面。
11. 前端路由。
12. 后端 API 请求。
13. GraphQL endpoint。
14. WebSocket endpoint。
15. SSE endpoint。
16. webhook 配置入口。
17. 文件上传入口。
18. 文件下载入口。
19. 导入入口。
20. 导出入口。
21. 预览入口。
22. 搜索入口。
23. 报表入口。
24. 用户资料入口。
25. 组织 / 租户 / 项目 / 工作区入口。
26. 权限管理页面。
27. invite / reset / verify / magic link 页面。
28. redirect / callback / return_url / next 参数入口。
29. 静态资源路径。
30. JS bundle。
31. sourcemap。
32. manifest。
33. service worker。
34. robots / sitemap / well-known。
35. health / metrics / debug / internal / legacy / example 路径。
36. localStorage。
37. sessionStorage。
38. IndexedDB。
39. Cookie 属性。
40. 安全响应头。
41. CORS 行为。
42. CSP 行为。
43. 控制台 error / warning。
44. 错误页面。
45. 页面缓存行为。
46. 浏览器后退、刷新、退出登录后的页面状态。

要求：

- 每一项尽量关联具体 URL、页面、按钮、表单、请求或参数。
- 找不到时写 unknown。
- 不允许编造。
- 访问失败时写 blocking_issue。
- 发现入口但暂时无法验证时写 verification_gap。
