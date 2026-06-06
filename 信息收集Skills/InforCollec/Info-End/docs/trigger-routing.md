# 触发路由表

| Skill | 高置信触发词 | 低置信触发词 | 禁止触发条件 | 误触发样例 | 漏触发样例 |
|---|---|---|---|---|---|
| 00-master | 信息暴露面动态验证、本机授权项目、证据闭环、运行态 | 泄露信息、看看有没有暴露 | 纯概念解释、写作整理、公网未知目标 | “解释信息暴露是什么” | “这个服务好像泄露配置” |
| 01-scope | 项目根目录、Base URL、端口、运行方式、账号角色、禁止范围 | 当前项目、服务已启动 | 已有完整输入且只做报告 | “给报告润色” | “localhost:3000 帮我查” |
| 02-runtime | ss/lsof/docker ps、监听端口、health/metrics/debug | 服务入口、运行中 | 服务未启动且只做静态 | “Docker 是什么” | “这个端口有什么信息” |
| 03-static | 路由提取、JS、source map、OpenAPI、GraphQL schema、配置、compose | 源码里找接口 | 无项目文件、要求确定动态结论 | “解释 axios” | “bundle 里有接口” |
| 04-dynamic | 动态验证、curl、HEAD/GET/OPTIONS、重复验证、响应摘要 | 访问看看、路径能不能读 | 破坏性 payload、外部 token 验证 | “压测接口” | “这个 /api/config 可读吗” |
| 05-role | 角色差异、低权限、管理员、浏览器存储、localStorage、IndexedDB | 登录前后、cookie | 无账号却要求角色结论 | “cookie 概念” | “普通用户能否看到导出” |
| 06-edge | 偏门、反思、遗漏、source map、service worker、cache、volume、错误面、导出 | 再深挖、剑走偏锋 | 第一轮未完成且无候选时直接报告 | “什么是 service worker” | “还有什么入口漏了” |
| 07-qg | 报告、脱敏、不可报告、质量门禁、QG、证据清单 | 整理结论 | 无证据却要求确定发现 | “美化标题” | “这个发现能不能提交” |
| 08-audit | 反向审查 Skills、文档保真、触发稳定、反幻觉、测试体系、评分 | 复盘刚才的 Skills | 用户只是执行项目审计 | “审计 localhost 信息暴露” | “刚才做的 Skills 哪里会失败” |
