# 08 自我审查与第二轮验证

完成第一轮后，进入自我审查。默认假设第一轮仍然遗漏了重要问题，并且可能存在证据分级错误。

请逐项回答：

1. 哪些 confirmed 证据不足，需要降级？
2. 哪些 finding 没有浏览器动作证据？
3. 哪些 finding 没有 network 请求证据？
4. 哪些 finding 没有响应差异或页面差异？
5. 哪些 finding 没有日志、数据库、trace、截图或 console 证据？
6. 哪些页面只测试了管理员，没有测试低权限用户？
7. 哪些页面只测试了同租户，没有测试跨租户？
8. 哪些页面只测试了自己的对象，没有测试他人对象？
9. 哪些接口只从前端正常点击测试，没有直接对 network 请求做输入变体？
10. 哪些入口只测试了成功路径，没有测试异常路径？
11. 哪些入口只测试了单请求，没有测试重复、乱序、并发？
12. 哪些列表、搜索、报表、导出、下载、预览没有验证权限一致性？
13. 哪些 PATCH / PUT / update 请求没有测试受保护字段覆盖？
14. 哪些 GraphQL 请求没有验证字段级权限？
15. 哪些 WebSocket 订阅没有验证跨用户、跨租户和权限变化？
16. 哪些缓存逻辑没有验证 user / role / tenant / object 维度？
17. 哪些 Cookie、localStorage、sessionStorage、IndexedDB 没有检查？
18. 哪些 service worker、浏览器缓存、后退缓存没有检查？
19. 哪些 JS bundle、sourcemap、静态资源没有检查？
20. 哪些错误页面、console、network error 没有检查敏感信息？
21. 哪些 redirect、callback、return_url、next 参数没有检查？
22. 哪些 invite、reset、verify、magic link 页面没有检查 token 绑定？
23. 哪些上传、下载、预览、导出入口没有检查对象绑定？
24. 哪些页面状态可能组成影响路径，但你只按单点处理？
25. 哪些测试缺少可自动化回归断言？

然后执行：

A. 证据不足的 confirmed 必须降级。
B. 为最高价值的 15 个 gap 设计补充测试。
C. 有执行条件的补充测试必须实际执行。
D. 无法执行的必须写明 blocking_issue。
E. 输出 delta_report。
