# basic-example

本示例展示最小合格输出写法。示例项目为虚构本地项目，不代表真实漏洞。

## 输入

```text
项目路径：C:\lab\demo-app
授权范围：C:\lab\demo-app、http://127.0.0.1:3000、Redis test DB 15、C:\lab\demo-app\test-output
运行方式：npm test；npm run dev；npm run worker:test
测试账号：admin_a、user_a、user_b
```

## 暴露面总表片段

| ID | 入口 | 数据来源 | 格式 | sink | 依赖/函数 | 权限要求 | 动态验证状态 | 结论 |
|---|---|---|---|---|---|---|---|---|
| DS-001 | `/admin/import-rules` | multipart file | YAML | `yaml.load` | js-yaml | admin | 未执行 | candidate |
| DS-002 | `/api/session/remember` | cookie | signed token | session wrapper | cookie-session | user | 已执行，签名阻断 | blocked |
| DS-003 | package dependency | 无入口 | 无 | node-serialize | node-serialize | 无 | 未调用 | dependency-only |

## DS-001 candidate 写法

1. 标题：admin import YAML 解析候选路径
2. 等级：中
3. 状态：candidate
4. 影响模块：规则导入
5. 输入入口：`POST /admin/import-rules`
6. 反序列化 sink：`yaml.load`
7. source 到 sink 调用链：`routes/admin.js -> services/ruleImport.js -> yaml.load(fileText)`
8. 安全控制：admin 权限，文件大小限制，未验证 schema 白名单
9. 绕过点或不足：未执行本地 marker 验证，不能判定触发
10. 动态验证命令：未执行
11. 正向样本：合法规则 YAML + harmless marker 字段
12. 负向样本：未知字段、错误类型、低权限用户、跨租户用户、非预期 content-type
13. 阻断样本：未知 YAML tag 应被拒绝
14. 观测证据：未验证
15. marker 证据：未验证
16. 日志证据：未验证
17. 清理动作：计划删除 `test-output/deserialization-markers/DS-001.txt`
18. 业务影响：若对象解析发生在 schema 校验前，可能导致规则导入逻辑被非预期字段影响
19. 修复建议：使用 safe loader；导入前做 schema；禁止动态 tag；签名和权限校验在解析前完成
20. 回归测试建议：`tests/admin-import-deserialization.spec.js`
21. 不足证据：缺本地执行、marker、日志、断言

## DS-002 blocked 写法

状态为 blocked，因为本地测试证明篡改 cookie 在进入 session 解析前被签名校验拒绝。报告中必须记录测试命令、请求样本、响应状态、日志和断言。没有这些证据时不能写 blocked。

## DS-003 dependency-only 写法

状态为 dependency-only，因为依赖文件存在 `node-serialize`，但未找到项目调用路径，也未找到来自 source 的参数流。不得报告为漏洞。
