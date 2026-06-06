# Final Evidence Court Rules

1. 没有文件证据：未证实。
2. 只有 Markdown 或矩阵：doc-only。
3. 只有 regex / keyword：candidate-only，不是语义审计。
4. 没有 AST backend：JS 审计能力不得声称 ready。
5. 没有 Source Map sourcesContent/sourceRoot/path 解析：Source Map 能力不得声称 ready。
6. 没有 Playwright/Burp/HAR/screenshot/request/response：未动态验证。
7. 没有 role/tenant replay：缺少多角色多租户验证。
8. 没有 schema validator：证据不可强校验。
9. 没有 report generator/report mapping：无法闭环到报告。
10. 没有 dashboard 读取真实产物：展示层伪闭环。
11. 没有 positive/negative/blocked/review 样本：测试不足。
12. 没有真实 OSS replay：工程可信度不足。
13. knowledge/templates 存在不等于已接入，必须有索引、路由和 hash baseline。
