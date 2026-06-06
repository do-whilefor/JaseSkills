# JS 审计保真度规则

1. Babel、TypeScript Compiler API、tree-sitter 只有在存在真实 backend 文件、调用方式、自检样本和 AST 输出时，才能写 `partial` 或 `ready`。
2. `source-sink`、`dataflow`、`taint tracking` 必须有 source、transform、sink、evidence 四段输出。只有关键词命中时只能写 `candidate-only`。
3. 动态验证必须包含请求、响应、账号/角色/租户、时间、截图或 HAR、三次复现或反证。没有这些时写 `未动态验证`。
4. 严重 JS 漏洞链必须拆成 detector。模板、知识条目、报告字段不等于 detector。
5. Role-only chunk、tenant-only endpoint、stale source map、Service Worker stale cache、BroadcastChannel、IndexedDB、Electron/Extension/WebView bridge 必须进入 needs_review，不能 silent ignore。
6. 评分时，文档、矩阵、模板、fixture、README 声明不能替代实现分。
