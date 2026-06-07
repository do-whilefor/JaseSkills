# 本地授权项目反序列化暴露面与动态验证报告

## 0. 报告元信息

| 字段 | 内容 |
|---|---|
| 项目名称 |  |
| 项目路径 |  |
| 授权边界 |  |
| 本地服务地址 |  |
| 测试账号/角色/租户 |  |
| 可写测试目录 |  |
| 报告时间 |  |
| 执行人/模型 |  |
| 结论版本 | 第一轮 / 反查后最终版 |

## 1. 执行摘要

- 项目语言：
- 框架：
- 运行方式：
- 反序列化相关依赖：
- 高风险入口数量：
- confirmed 数量：
- candidate 数量：
- blocked 数量：
- not reachable 数量：
- dependency-only 数量：
- false positive 数量：
- 最高风险点：
- 尚未覆盖原因：

## 2. 授权边界与禁止事项记录

| 项目 | 记录 |
|---|---|
| 允许访问的本地路径 |  |
| 允许访问的本地端口 |  |
| 允许使用的测试数据库/队列/缓存 |  |
| 允许写入的测试目录 |  |
| 禁止访问范围 | 公网、内网敏感地址、云元数据、生产系统、非授权服务 |
| 禁止 payload | 命令执行、恶意 gadget、外连、反弹、破坏文件/数据库、DoS、巨型 payload |
| 样本约束 | 无害 marker、canary、测试目录、临时表、可回滚事务、mock sink |

## 3. 项目结构与语言生态识别

### 3.1 语言与框架

| 证据 ID | 语言/框架 | 证据文件 | 判断依据 |
|---|---|---|---|
| EV-001 |  |  |  |

### 3.2 关键目录

| 目录类型 | 路径 | 是否存在 | 证据 |
|---|---|---:|---|
| API 路由 |  |  |  |
| controller / handler / service / middleware |  |  |  |
| model / entity / DTO |  |  |  |
| queue / job / task / worker |  |  |  |
| cache / session / auth |  |  |  |
| import / export / backup / restore |  |  |  |
| upload / file parser |  |  |  |
| plugin / extension / hook |  |  |  |
| test / fixture / seed |  |  |  |

### 3.3 依赖文件

| 证据 ID | 依赖文件 | 是否存在 | 说明 |
|---|---|---:|---|
| EV-DEP-001 | package.json / pnpm-lock / yarn.lock |  |  |
| EV-DEP-002 | pom.xml / build.gradle |  |  |
| EV-DEP-003 | composer.json / composer.lock |  |  |
| EV-DEP-004 | requirements.txt / pyproject.toml / Pipfile.lock |  |  |
| EV-DEP-005 | *.csproj / packages.config |  |  |
| EV-DEP-006 | Gemfile.lock |  |  |
| EV-DEP-007 | go.mod |  |  |

## 4. source 全量搜索记录

| Source ID | 类别 | 入口/文件 | 数据格式 | 权限/角色 | 搜索命令或定位方式 | 证据 |
|---|---|---|---|---|---|---|
| SRC-001 | HTTP body/query/path/header/cookie |  |  |  |  |  |
| SRC-002 | multipart 文件上传 |  |  |  |  |  |
| SRC-003 | JSON/XML/YAML/form-data/protobuf/msgpack |  |  |  |  |  |
| SRC-004 | session/remember-me/JWT-like token/自定义 token |  |  |  |  |  |
| SRC-005 | Redis/Memcached/cache blob |  |  |  |  |  |
| SRC-006 | Kafka/RabbitMQ/SQS/JMS/Celery/Sidekiq/queue job payload |  |  |  |  |  |
| SRC-007 | WebSocket message |  |  |  |  |  |
| SRC-008 | GraphQL variables |  |  |  |  |  |
| SRC-009 | webhook payload |  |  |  |  |  |
| SRC-010 | import/export 文件 |  |  |  |  |  |
| SRC-011 | backup/restore 文件 |  |  |  |  |  |
| SRC-012 | plugin/theme/extension 包 |  |  |  |  |  |
| SRC-013 | CLI 参数读取本地文件 |  |  |  |  |  |
| SRC-014 | 测试 fixture 被生产逻辑引用 |  |  |  |  |  |
| SRC-015 | 数据库 serialized blob 二次解析 |  |  |  |  |  |

## 5. sink 全量搜索记录

| Sink ID | 语言 | sink/函数/模式 | 文件路径 | 函数/方法 | 行号 | 搜索命令 | 证据 |
|---|---|---|---|---|---:|---|---|
| SNK-001 |  |  |  |  |  |  |  |

## 6. 依赖与框架风险映射

| 编号 | 依赖/模块 | 版本 | 相关反序列化能力 | 是否被项目调用 | 调用路径 | 输入来源 | 是否可动态验证 | 风险等级 | 证据 |
|---|---|---|---|---|---|---|---|---|---|
| DEP-001 |  |  |  | 是/否/未验证 |  |  | 是/否 | 高/中/低/无 |  |

判定规则：依赖存在但无调用为 dependency-only；有调用但无不可信输入为 not reachable；有 source 到 sink 可能路径但未动态验证为 candidate；安全控制阻断为 blocked；满足 confirmed 门槛才为 confirmed。

## 7. 暴露面总表

| ID | 入口 | 数据来源 | 格式 | sink | 依赖/函数 | 权限要求 | 动态验证状态 | 结论 |
|---|---|---|---|---|---|---|---|---|
| DS-001 |  |  |  |  |  |  | 未执行/已执行/失败/阻断 | confirmed/candidate/blocked/not reachable/dependency-only/false positive |

## 8. 每个问题详情

### DS-001 标题

1. 标题：
2. 等级：高 / 中 / 低 / 信息
3. 状态：confirmed / candidate / blocked / not reachable / dependency-only / false positive / 未验证
4. 影响模块：
5. 输入入口：
6. 反序列化 sink：
7. source 到 sink 调用链：
   - 文件：
   - 函数/方法：
   - 行号：
   - 参数传播：
   - 安全控制位置：
8. 安全控制：签名 / HMAC / 加密 / CSRF / 权限 / 租户 / safe loader / schema / 白名单 / 长度 / 来源限制 / 无
9. 绕过点或不足：
10. 动态验证命令：
11. 正向样本：
12. 负向样本：
13. 阻断样本：
14. 观测证据：
15. marker 证据：
16. 日志证据：
17. 清理动作：
18. 业务影响：
19. 修复建议：
20. 回归测试建议：
21. 不足证据：仅 candidate/未验证时填写

## 9. 动态验证执行记录

| 命令 ID | 工作目录 | 命令 | 输入样本 | 输出/日志 | 退出码 | 结论影响 |
|---|---|---|---|---|---:|---|
| CMD-001 |  |  |  |  |  |  |

| 请求 ID | 类型 | 目标 | 方法/协议 | 样本文件 | 响应证据 | 结论影响 |
|---|---|---|---|---|---|---|
| REQ-001 | HTTP/WebSocket/GraphQL/Queue/CLI/Cache |  |  |  |  |  |

| Marker ID | 路径/位置 | 触发方式 | 内容摘要 | 清理命令 | 清理结果 |
|---|---|---|---|---|---|
| MARKER-001 |  |  |  |  |  |

## 10. 补测清单

| Candidate ID | 测试入口 | 测试账号/权限 | 输入样本 | marker 设计 | 正向样本 | 负向样本 | 阻断样本 | 运行命令 | 观测位置 | 清理命令 | 预期结果 | 当前缺口 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DS-001 |  |  |  |  |  |  |  |  |  |  |  |  |

## 11. 降级清单

| 原结论 | 降级后结论 | Finding ID | 降级原因 | 缺少证据 | 后续补测 |
|---|---|---|---|---|---|
| confirmed | candidate |  | 缺少动态证据/marker/负向样本/清理/回归测试 |  |  |

## 12. 漏报追查清单

| 隐藏面 | 是否检查 | 证据 | 发现 | 未覆盖原因 |
|---|---:|---|---|---|
| session |  |  |  |  |
| remember-me |  |  |  |  |
| password reset |  |  |  |  |
| email verify |  |  |  |  |
| OAuth state |  |  |  |  |
| webhook |  |  |  |  |
| queue |  |  |  |  |
| failed job |  |  |  |  |
| dead-letter |  |  |  |  |
| cache |  |  |  |  |
| database serialized column |  |  |  |  |
| audit replay |  |  |  |  |
| event sourcing |  |  |  |  |
| import/export/backup/restore |  |  |  |  |
| plugin/theme/workflow/rule/report template |  |  |  |  |
| admin-only endpoint |  |  |  |  |
| CLI maintenance |  |  |  |  |
| test fixture production reference |  |  |  |  |
| legacy parser / migration parser / debug parser |  |  |  |  |
| parser fallback / content-type confusion |  |  |  |  |
| compressed/base64 nested payload |  |  |  |  |

## 13. 证据清单

| 证据 ID | 类型 | 文件/命令/请求 | 说明 | 可复现性 |
|---|---|---|---|---|
| EV-001 | 文件/命令/日志/marker/请求/断言 |  |  | 高/中/低 |

## 14. 修复建议

### P0

- 禁用危险反序列化。
- 使用 safe loader。
- 禁用 polymorphic default typing。
- 建立严格类型白名单。
- 签名验证必须在解析对象前完成。
- 不允许从 cookie/session/job/cache 中直接恢复任意对象。
- 使用 DTO / schema 解析，而不是任意对象解析。
- 队列消息必须有 schema、签名、版本、来源校验。
- import/backup/restore 必须隔离解析环境。
- 移除不必要的危险依赖。

### P1

- 加入 source/sink 单元测试。
- 加入反序列化安全回归测试。
- 加入依赖版本锁定和安全扫描。
- 加入日志审计。
- 加入类型解析告警。
- 加入异常输入速率限制。

### P2

- 重构历史 serialized blob。
- 迁移到安全数据格式。
- 为所有对象解析入口建立统一 adapter。

## 15. 强制自我反查

| 问题 | 答案 | 证据 | 修复或降级动作 |
|---|---|---|---|
| 是否只看了 controller，没有看 queue/cache/session/import/export/plugin/CLI | 是/否 |  |  |
| 是否把依赖存在误判成漏洞存在 | 是/否 |  |  |
| 是否把静态可疑误判成 confirmed | 是/否 |  |  |
| 是否缺少动态证据 | 是/否 |  |  |
| 是否没有测试负向样本 | 是/否 |  |  |
| 是否没有测试签名篡改、过期 token、低权限、跨租户 | 是/否 |  |  |
| 是否没有验证签名是在反序列化之前还是之后 | 是/否 |  |  |
| 是否忽略 base64/gzip/zip 包裹后的 serialized blob | 是/否 |  |  |
| 是否忽略数据库中存储后再解析的二阶段反序列化 | 是/否 |  |  |
| 是否忽略 failed job/dead-letter/retry payload | 是/否 |  |  |
| 是否忽略 import/backup/restore | 是/否 |  |  |
| 是否忽略 YAML/XML/JSON polymorphic type | 是/否 |  |  |
| 是否忽略 custom unmarshal/magic method/lifecycle hook | 是/否 |  |  |
| 是否用了不可接受的破坏性 payload | 是/否 |  |  |
| 是否没有给出可复现命令 | 是/否 |  |  |
| 是否没有给出 marker 证据 | 是/否 |  |  |
| 是否没有清理测试痕迹 | 是/否 |  |  |
| 是否没有说明修复后的回归测试 | 是/否 |  |  |
| 是否遗漏语言生态中的典型反序列化 sink | 是/否 |  |  |
| 是否需要补充更多隐藏暴露面 | 是/否 |  |  |

## 16. 最终验收结论

- 可交付状态：通过 / 不通过
- 不通过项：
- 降级后的最终状态统计：
- 仍未覆盖原因：
