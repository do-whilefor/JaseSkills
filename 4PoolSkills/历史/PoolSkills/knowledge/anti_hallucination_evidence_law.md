# 证据链法庭规则

1. 没有文件路径和代码位置的结论不得进入报告。
2. 没有 HAR、请求响应、截图、日志或等价运行态证据的严重漏洞不得 confirmed。
3. 没有负向控制的权限、租户、IDOR、GraphQL、WebSocket、业务逻辑问题不得 promoted。
4. 正则命中、工具告警、接口名猜测、错误回显只能是 candidate。
5. 失败、缺工具、缺登录态、缺多角色、多租户证据必须显式标记 blocked 或 needs_review。
