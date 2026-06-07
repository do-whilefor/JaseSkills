# Quality Gate

用于验收 `local-injection-verify` 输出是否满足 TXT 原文要求和工程化补强要求。

## 交付门禁

- [ ] 已读取原始 TXT。
- [ ] 已建立 TXT 到 Skill 映射表。
- [ ] 已区分原文复刻与工程化补强。
- [ ] 只保留 1 个主 Skill，没有拆出空壳 Skill。
- [ ] 命名为小写英文短横线，能体现本地授权注入动态验证。
- [ ] 无空目录、空文件、重复文件、装饰性文件。

## 授权与安全边界

- [ ] 报告说明只在本地授权环境、测试数据库、测试目录、测试账号、测试租户验证。
- [ ] 报告禁止公网敏感目标、破坏业务、删除数据、DoS/DDoS、长时间 sleep、破坏数据库、破坏文件系统、绕过授权范围。
- [ ] 报告说明中间人攻击不在范围内。
- [ ] 报告不含破坏性命令、真实敏感数据、真实 token/cookie、真实业务数据。

## 项目画像与矩阵

- [ ] 语言、框架、入口、路由、数据库、ORM、模板、表达式、搜索、队列/任务、缓存、文件、导入导出、GraphQL/WebSocket/RPC、依赖、高风险配置均有“已识别/未发现/需补充”。
- [ ] 注入暴露面矩阵包含编号、输入入口、参数名、参数类型、角色/租户、代码路径、sink、解释器/组件、安全处理、动态验证方式、状态。
- [ ] 每条候选点可追溯到 source-to-sink 路径。

## 输入面与 sink 覆盖

- [ ] HTTP query/body/path/header/cookie。
- [ ] JSON/XML/YAML/FormData/multipart。
- [ ] GraphQL query/variables/fragments、WebSocket、Webhook。
- [ ] 文件上传内容、文件名、MIME、压缩包内路径、CSV/Excel/PDF/HTML/Markdown。
- [ ] CLI、环境变量、后台任务、管理配置、模板预览、邮件/通知/报表模板。
- [ ] 搜索、排序、过滤、分组、分页、OAuth/SAML/OIDC、第三方集成、数据库二次读取字段。
- [ ] SQL/NoSQL/ORM raw、命令、模板、表达式、XPath/LDAP/XML、regex、JSONPath/JMESPath、GraphQL resolver、search DSL、Markdown/HTML/PDF、report/export/import、workflow/rule、cron/job、email/notification。

## 动态验证证据

- [ ] 每个验证有唯一 marker。
- [ ] 每个验证有正向请求或触发步骤。
- [ ] 每个验证有负向对照。
- [ ] 每个验证有预期安全行为和异常行为判定。
- [ ] 每个验证有日志、响应、数据库/文件/任务证据位置。
- [ ] 有状态改变的验证有回滚方式。
- [ ] 命令验证只使用本地无害 marker 输出或测试目录 marker 文件。
- [ ] SQL/NoSQL 只使用测试库、测试表、测试数据。
- [ ] 模板/表达式只证明 marker 被解释，不执行危险系统调用。
- [ ] 时间类验证单次延迟不超过 1 秒，并证明不是网络抖动。

## 结论分级

- [ ] 没有动态复现的结论未标为 confirmed。
- [ ] confirmed 有动态请求、响应或日志、marker、解释器处理证据、负向对照、最小复现、影响范围、修复建议、误报排除。
- [ ] high/critical confirmed 满足全部证据要求。
- [ ] 证据不足的结论已降级为 candidate、blocked 或 needs manual review。
- [ ] false positive 有安全机制证据。

## 二阶、隐藏参数与冷门路径

- [ ] 已追踪写入点 -> 存储位置 -> 触发点 -> sink -> marker 证据。
- [ ] 已检查用户资料、评论、备注、工单、审批、地址、订单、发票、标签、配置、模板、Webhook、OAuth/SAML/OIDC、导入文件、CSV/Excel、Markdown/HTML、管理配置、工作流、报表、邮件、日志字段。
- [ ] 已从前端 JS、sourcemap、OpenAPI/Swagger、GraphQL schema、DTO/model/schema、controller binding、validation schema、disabled field、localStorage/sessionStorage、feature flag、admin/test/dev/mobile/legacy API、webhook、import/export schema 提取隐藏参数。
- [ ] 已检查 CLI、cron、queue、import、migration、seed、maintenance、backup/restore、report、file converter、image processor、PDF generator、email sender、webhook retry worker、search indexer。

## 修复、回归与追溯

- [ ] 修复建议具体到代码层或组件层。
- [ ] 查询使用参数化和 allowlist 字段。
- [ ] 命令使用参数数组化并禁止 shell=True。
- [ ] 模板/表达式使用上下文隔离或沙箱。
- [ ] 搜索 DSL 使用 allowlist。
- [ ] 导出内容转义，二阶触发点统一编码。
- [ ] 每个 confirmed/candidate 有最小回归测试。
- [ ] 结论追溯到矩阵编号、计划编号、结果编号和证据编号。
- [ ] 没有把工程化补强伪装成 TXT 原文。
