# 02 浏览器验证基线

请使用浏览器自动化或等价方式建立 Web 验证基线。

必须记录：

1. 打开 Web base URL 的页面标题、状态码和截图。
2. 登录前可见页面、链接、按钮、表单、上传框、下载入口。
3. 登录后可见页面、链接、按钮、表单、上传框、下载入口。
4. 不同角色可见入口差异。
5. 不同租户可见入口差异。
6. 页面跳转路径。
7. 前端路由变化。
8. network 请求列表。
9. 每个关键请求的 method、URL、status、request params、response summary。
10. console error / warning。
11. localStorage 安全相关字段。
12. sessionStorage 安全相关字段。
13. IndexedDB 安全相关字段。
14. Cookie 属性：HttpOnly、Secure、SameSite、Domain、Path、Expires。
15. 安全响应头：CSP、X-Frame-Options、Referrer-Policy、Permissions-Policy、HSTS、X-Content-Type-Options。
16. service worker 注册情况。
17. cache storage 内容摘要。
18. sourcemap、JS bundle、静态资源暴露情况。
19. 错误页面和异常响应。
20. 退出登录后的页面、缓存、请求状态。

请尽量建立以下账号和数据视角：

1. anonymous。
2. user_low。
3. user_normal。
4. user_admin。
5. tenant_a_user。
6. tenant_b_user。
7. tenant_a_admin。
8. tenant_b_admin。
9. 自己的对象。
10. 他人的对象。
11. 同租户对象。
12. 跨租户对象。
13. archived 对象。
14. disabled 对象。
15. pending 对象。
16. soft_deleted 对象。

请尽量建立以下证据来源：

1. browser_trace。
2. screenshot。
3. console_log。
4. network_log。
5. request_log。
6. response_log。
7. cookie_snapshot_before。
8. cookie_snapshot_after。
9. storage_snapshot_before。
10. storage_snapshot_after。
11. service_worker_snapshot。
12. cache_snapshot。
13. local_callback_log。
14. mock_service_log。
15. service_log。
16. db_snapshot_before。
17. db_snapshot_after。

无法建立的项必须说明原因。
