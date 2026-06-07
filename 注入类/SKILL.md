---
name: local-injection-verify
description: Authorized local-project injection defect dynamic verification and reverse evidence audit. Use when the user has a local or explicitly authorized test target and wants injection exposure mapping, marker-based validation, evidence grading, second-order/hidden-entry review, and final downgrade of unsupported conclusions.
---

# Local Injection Verify

## 适用范围

用于本地已搭建、测试环境或明确授权范围内的项目。目标是把输入进入解释器、查询器、模板引擎、命令执行器、表达式引擎、序列化解析器、搜索 DSL、报表/导入导出引擎、队列或任务执行边界的路径，转成可审计的注入暴露面矩阵、动态验证计划、证据链和反查修正版报告。

仅允许使用测试数据库、测试目录、测试账号、测试租户、测试对象和可回滚事务。每次验证使用无害 marker。结论状态只能是 `confirmed`、`candidate`、`blocked`、`false positive`、`needs manual review`。

## 不适用范围

不得用于未授权公网目标、生产真实数据、破坏性验证、中间人攻击、DoS/DDoS、长时间 sleep、删除或破坏数据、破坏数据库、破坏文件系统、绕过授权范围、读取真实敏感数据、项目目录外非测试位置写入。没有动态证据时不得输出 `confirmed`，没有完整证据时不得输出 high/critical confirmed。

## 输入要求

| 输入项 | 必需性 | 用途 | 缺失处理 |
|---|---|---|---|
| 本地项目路径 | 必需 | 读取代码、配置、依赖、路由、任务和测试入口 | `blocked`，不得猜测项目结构 |
| 启动命令或本地服务地址 | 必需 | 发起动态请求、触发任务、采集响应 | `blocked` 或 `needs manual review` |
| 测试数据库或回滚方式 | 必需 | SQL/NoSQL、二阶、导入导出验证 | 只能 `candidate`，不得 `confirmed` |
| 测试账号、角色、租户矩阵 | 必需 | 验证匿名、普通、管理员、租户 A/B、API token、Webhook 身份 | 标记角色/租户覆盖不足 |
| 日志位置或日志命令 | 必需 | 证明解释器处理、错误栈、拦截、参数化 | 无日志时不得 high/critical confirmed |
| 允许写入的测试目录 | 条件必需 | 命令、文件、导入导出、marker 文件验证 | 缺失时禁止写入类验证 |
| OpenAPI/Swagger、GraphQL schema、前端 bundle、sourcemap | 可选但优先 | 提取隐藏参数、未暴露接口、schema 字段 | 记录未覆盖来源 |
| CLI、队列、任务、导入导出触发方式 | 条件必需 | 非 HTTP 与异步二阶验证 | 缺失时 `needs manual review` |

## 输出要求

必须输出“反查修正版注入类缺陷报告”，至少包含：0 授权与安全边界确认；1 项目运行画像；2 注入暴露面矩阵；3 动态验证计划；4 动态验证结果；5 二阶注入专项结果；6 隐藏参数与冷门入口结果；7 依赖与封装风险；8 高价值漏洞候选清单；9 confirmed 漏洞清单；10 修复建议；11 回归测试建议；12 反查修正版报告；13 真实授权评估仍可能漏掉严重注入类缺陷的具体原因。

## 原文复刻规则

以下为 TXT 原文要求转化成的硬规则：

1. 角色不是普通代码审计助手，而是“授权本地项目注入类缺陷动态验证负责人”，反查阶段切换为“注入类漏洞反向审判官 / 动态验证证据审计官 / 误报追责官 / 二阶注入专项猎手 / 冷门输入面审查官”。
2. 任务不是泛泛扫描，也不是只做静态审计；必须围绕代码、项目结构、依赖、运行时路由、数据库、模板、消息队列、后台任务、CLI、文件导入导出、Webhook、GraphQL、REST API、管理端功能、前端隐藏参数建立暴露面并动态验证。
3. 先建立项目运行画像，再找候选点。画像必须覆盖语言、框架、入口文件、路由注册、数据库、ORM、模板引擎、表达式引擎、搜索引擎、消息队列、缓存、任务调度、文件处理、导入导出、GraphQL/WebSocket/RPC。
4. 外部输入必须覆盖 HTTP query/body/path/header/cookie、JSON/XML/YAML/FormData/multipart、GraphQL query/variables/fragments、WebSocket、Webhook、文件上传内容/文件名/MIME/压缩包内路径/CSV/Excel/PDF/HTML/Markdown、CLI、环境变量、后台任务、管理后台配置、模板预览、邮件/通知/报表模板、搜索/排序/过滤/分组/分页、OAuth/SAML/OIDC、第三方集成、数据库存储后再次读取执行字段。
5. 危险 sink 必须覆盖 SQL/NoSQL/ORM raw query、shell/command/process spawn、template render、表达式语言、XPath/LDAP/XML parser、regex、JSONPath/JMESPath、GraphQL resolver 拼接、search query DSL、server-side include、Markdown/HTML renderer、YAML/XML/JSON 反序列化配置、report/export engine、workflow/rule engine、cron/job expression、email/template notification renderer。
6. 必须建立 source-to-sink 数据流图：source、参数名、参数类型、controller/service/model/helper/wrapper 路径、校验/编码/转义/参数化、最终解释器、可触发角色、跨租户/跨角色/二阶触发。
7. 每个验证必须在本地启动项目，使用测试数据库或可回滚事务，使用测试账号/租户/对象，使用唯一 marker，具备正向请求、负向对照、安全结果、日志、HTTP 请求响应、数据库/文件/任务前后对比、服务端错误栈、最小复现步骤。
8. 禁止破坏性 payload；命令验证只允许本地无害 marker 输出或测试目录 marker 文件；SQL/NoSQL 只允许测试库、测试表、测试数据；模板/表达式只允许证明 marker 被解释，不执行危险系统调用；时间类单次延迟不得超过 1 秒并证明不是网络抖动。
9. 注入类型至少覆盖 SQL、NoSQL、命令/参数、模板/表达式、XPath/LDAP/XML、GraphQL、Header/CRLF、JSONPath/JMESPath/Regex/Search DSL、Import/Export、二阶注入。
10. 必须额外检查隐藏参数、非主流程入口、封装与依赖、多解释器链、类型边界、权限组合。
11. confirmed high/critical 必须有动态请求证据、响应或日志证据、marker 被解释/拼接/执行/越权查询或跨边界影响证据、负向对照、最小复现、影响范围、修复建议、误报排除。
12. 反查阶段必须审判所有 confirmed。缺少启动、请求、正向样本、负向对照、marker、日志、数据库/文件/任务证据、解释器处理证据、正常功能排除或回滚方案时，必须降级为 `candidate`。
13. 反查阶段必须重新枚举 24 类解释器、15 类二阶字段、16 类隐藏参数来源、10 类封装、10 类角色/租户身份、15 类非 HTTP 入口、20 类冷门检查点。
14. 最终必须列出被降级结论、新候选、漏掉的动态验证项、二阶路径、隐藏参数、解释器边界、角色/租户组合、需要补做的最小验证命令或请求、最终 confirmed/candidate/false positive/blocked 清单，以及仍可能漏掉严重问题的具体原因。

## 工程化补强规则

以下为执行补强，不冒充 TXT 原文：

1. 候选点编号使用 `INJ-EXP-###`，计划编号使用 `PLAN-INJ-###`，结果编号使用 `RESULT-INJ-###`。
2. marker 格式使用 `INJ_MARKER_<UTC时间>_<6位随机串>`。
3. 证据编号使用 `EVID-###`，记录类型、采集时间、路径、请求摘要、脱敏状态和可复核方式。
4. 每个结论必须引用矩阵编号、计划编号、结果编号和证据编号。不能引用时不得 `confirmed`。
5. 输出中真实 token、cookie、密码、个人数据、业务数据必须替换为 `<REDACTED>`。
6. 修复建议必须绑定代码路径或组件；无法定位时写“修复点未定位”。
7. 回归测试必须包含安全输入、异常输入、预期安全行为、断言点、回滚方式。
8. `source/original-txt.txt` 保存原 TXT；`mappings/txt-skill-map.md` 保存映射表。

## 核心工作流

1. 边界确认：记录授权范围、测试库、测试目录、测试账号、测试租户、回滚方式和禁止行为。
2. 项目画像：从依赖、配置、入口、路由、ORM、模板、队列、任务、文件、搜索、日志中提取运行画像。
3. 输入面枚举：枚举 HTTP、GraphQL、WebSocket、Webhook、文件、CLI、环境变量、后台任务、管理配置、模板预览、搜索排序过滤、OAuth/SAML/OIDC、第三方集成、二次读取字段。
4. 解释器边界枚举：枚举 SQL、NoSQL、ORM raw、命令、模板、表达式、搜索 DSL、GraphQL resolver、XPath、LDAP、XML、JSONPath/JMESPath、regex、report/export/import、workflow/rule、email/notification、Markdown/HTML/PDF、queue、scheduled job、CLI、config、logging query。
5. source-to-sink 建模：为每条路径记录参数、代码路径、安全处理、最终 sink、角色/租户、二阶触发。
6. 输出暴露面矩阵：每个候选点保留状态，不能因为证据不足删除。
7. 设计动态验证计划：为每个候选点写正向请求、负向对照、marker、预期安全行为、异常判定、证据位置、回滚、风险控制。
8. 执行或记录受阻：能执行则采集证据；不能执行则写 `blocked` 或 `needs manual review`。
9. 证据分级：按证据分为 confirmed、candidate、blocked、false positive、needs manual review。
10. 二阶与冷门专项：检查写入点、存储、触发、异步、隐藏参数、非主流程、封装、多解释器链、类型边界。
11. 反向审判：复查所有 confirmed 和 high/critical，证据缺口触发降级。
12. 最终报告：输出清单、修复、回归测试和仍可能漏掉的问题。

## 分阶段执行步骤

### 阶段 0：边界确认

输出授权范围、本地路径、服务地址、测试库、账号/租户、测试目录、日志位置、回滚方式、禁止行为、缺失项。授权或回滚缺失时，不执行动态确认。

### 阶段 1：项目运行画像

读取项目根目录、依赖声明、配置、启动脚本、路由、ORM、模板、队列、任务、GraphQL/WebSocket/RPC、文件处理、搜索、日志。每项结果必须为“已识别 / 未发现 / 需补充”，并给证据来源路径。

### 阶段 2：输入面与 sink 枚举

从路由、controller、resolver、DTO/model/schema、验证器、前端 bundle、sourcemap、OpenAPI/Swagger、GraphQL schema、webhook schema、CLI、任务、导入导出、模板、管理后台提取 source 和 sink，填入矩阵。

### 阶段 3：动态验证计划

对每个 `INJ-EXP-###` 生成 marker，定义正向请求、负向对照、预期安全行为、异常行为、证据位置、前后对比、回滚方式和风险控制。缺少任一关键字段时不得进入 confirmed 判定。

### 阶段 4：动态验证与分级

采集请求、响应、日志、错误栈、数据库/文件/队列/任务证据。confirmed 必须证明 marker 被解释器处理或被安全机制拦截前后的差异；candidate 只证明代码路径或部分证据；false positive 必须证明安全处理；blocked 必须说明缺失条件。

### 阶段 5：反查修正

逐项复查 confirmed、high/critical、未验证解释器、二阶字段、隐藏参数、封装、角色/租户、非 HTTP 入口和冷门检查点。发现证据不足立即降级，补写最小验证步骤。

## 质量门禁

1. 未确认本地授权、测试库、测试目录、测试账号、测试租户、回滚方式，不得 confirmed。
2. 未建立项目运行画像，不得输出最终结论。
3. 未建立 TXT 到 Skill 映射，不得通过交付。
4. 未区分原文复刻和工程化补强，不得通过交付。
5. 未输出注入暴露面矩阵，不得通过报告。
6. 矩阵缺输入入口、参数名、类型、角色/租户、代码路径、sink、解释器、安全处理、动态验证方式、状态，不得通过报告。
7. confirmed 缺请求、响应/日志、marker、负向对照、解释器处理证据、影响范围、回滚、误报排除时，必须降级。
8. SQL 之外的模板、命令、搜索 DSL、GraphQL、二阶、隐藏参数、非 HTTP 入口没有覆盖记录时，不得通过。
9. high/critical confirmed 必须满足严重性 8 项证据。
10. 不得输出破坏性步骤、真实敏感数据、真实 token/cookie、危险命令或公网目标攻击步骤。
11. 每个 confirmed/candidate 必须有最小回归测试。
12. 报告结论必须追溯到矩阵编号、计划编号、结果编号和证据编号。

## 幻觉控制

不得把静态怀疑写成动态确认。不得编造组件、路由、账号、日志、数据库证据、请求或 marker。没有读取到文件写“未验证”。没有启动项目写“未动态验证”。没有负向对照、marker 或解释器处理证据时不得 confirmed。工程化补强必须标注来源，不得写成原文要求。

## 失败处理

| 失败场景 | 状态 | 处理方式 | 禁止行为 |
|---|---|---|---|
| 无项目路径 | blocked | 要求补充本地路径 | 不得推测结构 |
| 项目无法启动 | blocked / needs manual review | 记录启动失败和最小修复输入 | 不得伪造请求 |
| 无测试库或回滚 | candidate / blocked | 只输出静态候选和验证计划 | 不得 confirmed |
| 无账号/租户矩阵 | blocked | 标记角色覆盖不足 | 不得假设权限 |
| 无日志 | candidate | 采集响应并标记日志缺失 | 不得 high/critical confirmed |
| 需要人工触发 | needs manual review | 写最小人工验证步骤 | 不得伪造触发结果 |
| 安全机制已拦截 | false positive | 记录参数化/转义/allowlist 证据 | 不得保留 confirmed |
| 验证会越界或破坏 | blocked | 停止并改为安全计划 | 不得执行危险动作 |

## 输出格式

使用 `templates/output-template.md`，字段不得留空。没有结果时写 `未发现证据`、`未验证`、`blocked` 或 `不适用`。

## 自检清单

- [ ] 已确认授权边界、测试库、测试目录、测试账号、测试租户、回滚方式。
- [ ] 未访问公网敏感目标，未破坏数据，未执行 DoS/DDoS 或长时间 sleep。
- [ ] 已建立项目运行画像。
- [ ] 已枚举外部输入来源和危险 sink。
- [ ] 已建立 source-to-sink 数据流图和暴露面矩阵。
- [ ] 每个候选点都有正向请求、负向对照、marker、证据位置、回滚方式。
- [ ] SQL、NoSQL、命令、模板/表达式、XPath/LDAP/XML、GraphQL、Header/CRLF、JSONPath/JMESPath/Regex/Search DSL、Import/Export、二阶注入都有覆盖记录。
- [ ] 隐藏参数、非主流程、封装依赖、多解释器链、类型边界、角色租户都有覆盖记录。
- [ ] 所有 confirmed 均有动态证据链；证据不足已降级。
- [ ] 已输出修复建议、回归测试和反查修正版报告。
- [ ] 已回答真实授权评估仍可能漏掉严重问题的具体原因。

## TXT 到 Skill 映射说明

完整映射表在 `mappings/txt-skill-map.md`。执行时必须区分：`原文复刻` 为 TXT 中已有角色、范围、流程、禁止事项、覆盖类型、输出章节和反查要求；`工程化补强` 为编号、证据字段、门禁、失败处理、追溯文件、模板和测试。任何新增字段不得伪装成 TXT 原文。
