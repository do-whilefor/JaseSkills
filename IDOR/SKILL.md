# local-object-access-audit

## 适用范围

本 Skill 只用于用户本地搭建、用户明确授权测试的开源项目或本地测试环境。目标是对对象引用访问控制缺陷做动态验证，覆盖对象归属校验缺失、资源访问越界、水平越权、垂直越权、多租户隔离缺陷，以及后端接受前端未暴露参数导致的访问控制绕过。

启动前必须同时满足：

1. 用户提供本地项目路径、仓库目录、容器名、服务地址或测试环境说明。
2. 用户确认目标不是公网第三方资产。
3. 用户允许创建或使用本地测试账号、本地测试数据、marker 文件、测试租户和测试角色。
4. 用户提供回滚方式，或接受写操作、删除、状态变更全部标记为 `blocked`。
5. 证据目录可写，能够保存请求、响应、账号说明、资源归属证明、日志、截图、HAR 或代码片段。

## 不适用范围

出现任一情况时禁止执行动态验证：

1. 目标是公网真实站点、第三方资产、未知归属系统或未授权系统。
2. 用户要求扫描、爆破、枚举不可控目标。
3. 用户要求读取真实用户隐私数据。
4. 用户要求破坏数据库、删除业务数据，或绕过授权边界之外的系统。
5. 用户无法提供本地测试账号、测试租户、测试数据或可回滚环境。
6. 用户要求把未执行、无证据或只有静态可疑的内容写成 `confirmed`。

不满足适用范围时，输出失败处理结果；不得生成漏洞确认结论。

## 输入要求

| 输入项 | 必填 | 格式 | 用途 | 缺失处理 |
|---|---:|---|---|---|
| `project_path` | 是 | 本地路径 | 读取项目结构、代码、路由、模型、前端资源 | 停止执行并输出缺失项 |
| `local_base_url` | 是 | `http://127.0.0.1:port`、`http://localhost:port` 或本地容器地址 | 发起真实请求 | 动态验证标记 `blocked` |
| `test_accounts` | 是 | `user_a`、`user_b`、`manager_a`、`admin_local`、`anonymous` | 多账号矩阵测试 | 缺失账号对应矩阵标记 `not_run` |
| `test_tenants` | 是 | `tenant_a`、`tenant_b` | 多租户隔离验证 | 跨租户结论不得为 `confirmed` |
| `test_resources` | 是 | 每类关键资源至少 tenant_a 两个、tenant_b 两个 | 替换对象引用并证明归属 | 先生成 fixture；不能生成则 `not_run` |
| `rollback_method` | 是 | seed、事务、快照、测试库、volume 备份 | 防破坏与回滚 | 写操作、删除、状态变更标记 `blocked` |
| `evidence_dir` | 是 | 本地目录 | 保存证据 | 不可写时停止 `confirmed` 判断 |
| `run_id` | 否 | 时间戳或短 ID | 关联证据 | 缺失时生成本地时间戳 |

测试身份必须记录：

| 身份 | 角色 | 租户 | 用途 |
|---|---|---|---|
| `user_a` | 普通用户 | `tenant_a` | 正向访问 tenant_a 资源；越界请求 tenant_b 资源 |
| `user_b` | 普通用户 | `tenant_b` | 正向访问 tenant_b 资源；作为越界目标 |
| `manager_a` | tenant_a 管理角色 | `tenant_a` | 验证垂直越权和管理边界 |
| `admin_local` | 本地测试管理员 | local/admin | 准备测试数据、读取归属证明；不得直接用于判定普通越权 |
| `anonymous` | 未登录 | 无 | 验证登录态边界 |

## 输出要求

最终报告必须包含：

1. 运行边界和授权说明。
2. 项目结构识别结果。
3. 访问控制暴露面矩阵。
4. 测试身份、测试数据、资源归属证明。
5. 真实请求清单。
6. 动态验证结果摘要。
7. `confirmed`、`blocked`、`candidate`、`false_positive` 四类结果。
8. 每个 `confirmed` 的复现步骤、原始请求、原始响应关键片段、账号说明、资源归属证明、代码根因、前端限制不足、服务端校验缺失、curl 或脚本、修复建议、修复后验证方法、严重程度与理由。
9. 反向审计 15 问逐条回答。
10. 遗漏路径清单。
11. 非常规路径补测结果。
12. 修复优先级。
13. 回归测试脚本或脚本模板。
14. 对所有 `not_run`、`blocked`、`failed` 的原因说明。

## 原文复刻规则

以下内容直接来自 TXT，执行时不得弱化、替换为口号或改成静态总结：

1. 只在本地搭建、用户有授权测试的开源项目中工作。
2. 不得访问公网目标，不得扫描第三方资产，不得读取真实用户隐私数据，不得破坏数据库，不得删除业务数据，不得绕过授权边界之外的系统。
3. 所有验证必须使用本地测试账号、本地测试数据、可回滚数据库、marker 文件、测试租户和测试角色完成。
4. 目标是系统性发现并动态验证对象归属校验缺失、资源访问越界、水平越权、垂直越权、多租户隔离缺陷、后端接受前端未暴露参数导致的访问控制绕过。
5. 重点是动态验证；不允许只给静态猜测。
6. 暴露面建模必须覆盖后端路由、API endpoint、GraphQL resolver、WebSocket 事件、RPC 方法、后台管理接口、文件下载接口、导出接口、预览接口、Webhook、回调接口。
7. 前端识别必须覆盖隐藏 API、未在 UI 展示但存在的参数、注释路径、source map、懒加载 chunk、移动端入口、管理端入口、内部端入口。
8. 数据模型识别必须覆盖用户、组织、团队、租户、项目、订单、文件、消息、审批、邀请、token、session、绑定关系、共享关系。
9. 权限代码识别必须覆盖 auth middleware、policy、guard、decorator、scope、tenant filter、owner check、serializer、repository、ORM query、service 层校验。
10. 用户可控对象引用参数必须覆盖 `id`、`uuid`、`slug`、`key`、`path`、`filename`、`user_id`、`org_id`、`tenant_id`、`team_id`、`project_id`、`order_id`、`file_id`、`message_id`、`workspace_id`、`account_id`、`resource_id`、`parent_id`、`owner_id`、`created_by`、`assignee_id`、`email`、`phone`、`username`。
11. 框架默认行为必须检查路由绑定、ORM 自动查询、序列化、批量更新、参数合并、JSON body 覆盖 query 参数、multipart 参数解析、method override、GraphQL alias/batching、WebSocket room join、缓存 key 生成。
12. 暴露面矩阵字段必须包含：入口位置、方法/协议、参数名、资源类型、资源归属字段、当前登录角色、目标资源所属角色/租户、权限判断位置、是否存在服务端归属校验、是否需要动态验证、风险原因、证据路径。
13. 最小测试身份必须包含 `user_a`、`user_b`、`manager_a`、`admin_local`、`anonymous`。
14. 最小测试数据必须包含 tenant_a 至少 2 个资源对象、tenant_b 至少 2 个资源对象；每类关键资源记录 `owner_id`、`tenant_id`、`org_id`、`visibility`、`status`；所有测试数据可回滚；只允许读取测试资源或 marker 内容。
15. 动态验证方法必须覆盖浏览器自动化、API replay、多账号矩阵、参数差异、批量接口、GraphQL、WebSocket、文件类接口、缓存类、后端接受性测试。
16. 每一个候选问题必须同时做正向、反向、越界尝试和阻断验证。
17. 只有替换对象引用参数后，无权限角色成功读取、修改、导出、下载、订阅或影响他人资源，才允许标记为 `confirmed`。
18. 不得标记为 `confirmed` 的情况：只有代码可疑、只有 200 空响应、只有前端隐藏按钮、只有报错差异、管理员正常权限、本地测试数据配置错误、无法证明资源归属、未保存请求响应账号归属数据库记录或日志证据。
19. 高影响只允许用于 TXT 指定条件：跨用户或跨租户非公开资源读取；修改、删除、审批、转移、导出、下载他人资源；批量越界；组织/团队/租户边界绕过；影响资金、订单、审批、权限、邀请、账号绑定、文件、消息、审计日志；后端接受越权字段；缓存、异步任务、导出任务、WebSocket、GraphQL resolver 造成跨用户或跨租户泄露。
20. 偏门路径必须覆盖：列表/详情过滤不一致、更新覆盖 owner_id/tenant_id、删除弱校验、导出下载预览弱校验、隐藏管理 API、GraphQL nested resolver、WebSocket room/topic、异步 task_id、文件路径附件临时 URL、分享邀请重置 token、搜索自动补全统计、批量只校验第一个 id、PATCH/PUT 未暴露字段、method override、缓存 key、路由模型自动绑定、ORM include/preload/populate、软删除归档草稿历史审计、移动端旧版 debug internal、webhook 导入报表通知中心。
21. 最终报告必须分为 `confirmed`、`blocked`、`candidate`、`false_positive`。
22. 每个 `confirmed` 必须包含：漏洞编号、影响资源、受影响接口、受影响角色、越界方向、最小复现步骤、原始请求、原始响应关键片段、测试账号说明、测试资源归属证明、代码根因位置、为什么前端限制无效或不足、为什么服务端校验缺失、可复现脚本或 curl、修复建议、修复后验证方法、严重程度与理由。
23. 必须边做边记录证据；不得编造请求、响应、文件路径、行号、测试结果；没有实际执行写 `not_run`；执行失败写失败原因；不确定项降级为 `candidate`。
24. 初轮后必须作为自己的审计官反向审查 15 个问题，覆盖 UI 外接口、方法类型、参数位置、角色矩阵、资源归属证明、200 空响应、管理员权限、批量逐项权限、缓存/任务/token 绑定、ORM 关联、未暴露字段、GraphQL、WebSocket、软删除历史审计通知搜索统计、完整证据。
25. 遗漏路径清单字段必须包含：漏掉的入口、为什么第一轮会漏、需要补测的具体请求、需要使用哪个测试账号、需要替换哪个对象引用字段、预期安全结果、如果失败代表什么缺陷、执行状态、证据文件路径。
26. 非常规路径补测必须覆盖旧/废弃/兼容/移动/admin/internal 接口、前端未使用但后端注册路由、自动生成 CRUD、REST 与 GraphQL 权限一致性、API 直接请求、列表与详情导出下载统计、创建与更新归属、批量逐项、子资源附件评论消息历史版本、include/expand/populate、异步任务、method override/content-type/multipart/JSON merge patch、已知 UUID、缓存、事务状态机审批邀请分享绑定流程。
27. 每条补测路径必须给真实执行结果；没有执行写 `not_run`，不得推测成结论。

## 工程化补强规则

以下规则为使 TXT 可执行而新增；输出报告时必须标记为工程化补强，不得说成 TXT 原文：

1. 为每次运行生成 `run_id`，所有证据文件名包含 `run_id`、入口编号、账号和测试类型。
2. 执行状态使用 `done`、`not_run`、`blocked`、`failed`；结果分类使用 `confirmed`、`blocked`、`candidate`、`false_positive`。两类字段不得混用。
3. 每个动态请求至少保存 `request`、`response`、`ownership_proof`；定位根因时保存 `code_excerpt`。
4. 请求证据可脱敏，但必须保留方法、路径、参数名、对象引用值、账号角色、响应状态、响应关键字段、marker 内容。
5. 修改类验证必须保存 before、request、response、after、rollback。
6. 删除类验证默认不执行真实删除；仅允许对临时 marker 资源在可回滚事务或测试库中验证。
7. `admin_local` 只用于环境准备和归属证明；普通用户越权不能用 `admin_local` 结果替代。
8. 无证据路径的结论只能是 `candidate`、`not_run`、`blocked` 或 `failed`。
9. 回归脚本必须使用本地 base URL、本地测试账号、本地测试资源 ID；不得包含公网目标。
10. 项目不存在 GraphQL、WebSocket、导出、缓存等机制时，也必须在遗漏路径或非常规补测中写明识别依据并标记 `not_run` 或 `blocked`。

## 核心工作流

1. 确认运行边界：本地授权、测试账号、测试数据、回滚方式、证据目录。
2. 读取项目结构：语言、框架、路由文件、前端构建产物、数据库模型、权限中间件、服务层、ORM 查询、测试目录。
3. 生成访问控制暴露面矩阵。
4. 创建或确认五类身份和双租户资源，保存归属证明。
5. 从浏览器、HAR、日志、测试用例、路由表、前端 JS、source map、GraphQL schema、WebSocket 客户端代码中提取真实请求。
6. 为每个对象引用入口构造正向、反向、越界、阻断验证。
7. 发起真实请求并保存证据。
8. 依据证据归类为四类结果。
9. 逐条回答反向审计 15 问，生成遗漏路径清单。
10. 对非常规路径补测或标记 `not_run`、`blocked`、`failed`。
11. 输出修复优先级和回归测试脚本。
12. 执行最终自检；有问题时修复报告或降级结论。

## 分阶段执行步骤

### 阶段 0：运行边界确认

输入：`project_path`、`local_base_url`、测试账号、测试数据说明、回滚方式、`evidence_dir`。

执行：

1. 判断 `local_base_url` 是否为 localhost、127.0.0.1、本地容器地址或用户明确声明的本地授权地址。
2. 检查证据目录可写。
3. 记录五类账号、两个租户和回滚方式。
4. 若目标指向公网第三方资产，停止动态验证。

输出：`run-boundary.md`。

通过标准：必要输入存在，目标属于本地授权测试环境，证据目录可写。

失败处理：缺少关键输入时停止；缺测试账号时只做可执行的静态暴露面建模，并将相关动态验证标记 `not_run`。

### 阶段 1：项目结构与暴露面建模

输入：`project_path`。

执行：

1. 枚举后端路由、API、GraphQL resolver、WebSocket、RPC、后台接口、文件接口、Webhook、回调接口。
2. 枚举前端 JS、source map、懒加载 chunk、隐藏 API、注释路径、移动端、管理端、内部端入口。
3. 枚举数据库模型和对象归属字段。
4. 枚举权限中间件、policy、guard、decorator、scope、tenant filter、owner check、serializer、repository、ORM query、service 层校验。
5. 枚举用户可控对象引用参数和参数位置。
6. 枚举框架默认行为风险点。

输出：访问控制暴露面矩阵。

通过标准：每个入口至少记录 12 个 TXT 要求字段和证据路径。

失败处理：无法识别的入口不删除，标记为 `candidate`，证据路径写识别失败原因。

### 阶段 2：测试身份与测试数据准备

输入：`test_accounts`、`test_tenants`、`test_resources`、`rollback_method`。

执行：

1. 确认 user_a/tenant_a、user_b/tenant_b、manager_a/tenant_a、admin_local、anonymous。
2. 为 tenant_a 和 tenant_b 各创建或确认至少 2 个资源对象。
3. 每类关键资源记录 `owner_id`、`tenant_id`、`org_id`、`visibility`、`status`、marker。
4. 保存数据库记录、fixture 文件或 admin_local 查询结果作为归属证明。
5. 标记测试资源并记录回滚方式。

输出：`test-data-manifest.md` 与 `ownership-proofs/`。

通过标准：每个被测对象引用值都有归属证明。

失败处理：没有归属证明时，相关结果不得为 `confirmed`。

### 阶段 3：真实请求提取

输入：暴露面矩阵、浏览器 HAR、日志、路由表、前端 JS、测试用例。

执行：

1. 提取 UI 中真实请求。
2. 提取 JS 中存在但 UI 未展示的请求。
3. 提取后端注册但前端未使用的请求。
4. 提取 GraphQL query、mutation、subscription。
5. 提取 WebSocket room、topic、event、payload。
6. 提取导出、下载、预览、缩略图、异步任务、缓存相关请求。
7. 标记对象引用位置：path、query、JSON body、form-data、header、cookie、GraphQL variable、WebSocket payload。

输出：`request-inventory.md`。

通过标准：每条请求对应入口编号、对象引用字段和证据来源。

失败处理：无法重放的请求保留为 `candidate`，写明缺失 session、CSRF、fixture 或协议客户端。

### 阶段 4：多账号动态验证

输入：`request-inventory`、测试账号、测试资源。

执行：

1. 正向验证：资源所有者或有权限角色访问自己的资源。
2. 反向验证：无权限角色访问同一资源，应返回 401、403、404 或业务拒绝。
3. 越界尝试：替换对象引用参数，验证无权限角色是否能读取、修改、导出、下载、订阅或影响他人资源。
4. 阻断验证：修复或加入权限校验后，重放同一请求必须失败。
5. 保存 request、response、资源归属证明、账号说明、日志或截图。

输出：`dynamic-verification-results.md`。

通过标准：每个候选问题都有正向与反向结果；`confirmed` 必须有越界成功证据。

失败处理：状态码 200 但内容为空或无 marker，归类为 `blocked` 或 `candidate`，不得 `confirmed`。

### 阶段 5：结果分类

输入：动态验证证据。

执行：

1. 有真实越界访问或影响证据，且有资源归属证明，归入 `confirmed`。
2. 动态验证证明服务端正确拒绝，归入 `blocked`。
3. 代码或暴露面可疑但证据不足，归入 `candidate`。
4. 经验证符合角色设计、无越界数据或属于本地配置问题，归入 `false_positive`。

输出：四类结果。

通过标准：每条结果有证据路径；`confirmed` 字段完整。

失败处理：字段缺失的 `confirmed` 降级为 `candidate`。

### 阶段 6：反向审计与遗漏补测

输入：初轮结果。

执行：

1. 逐条回答 15 个反向审计问题。
2. 生成遗漏路径清单。
3. 对遗漏路径继续补测，特别是非常规路径。
4. 为每条补测路径写执行状态：`done`、`not_run`、`blocked`、`failed`。
5. 未执行项不得推测结论。

输出：`missed-paths-review.md` 与 `unusual-path-results.md`。

通过标准：15 个反查问题均有明确回答；每条非常规路径都有真实执行状态。

失败处理：无证据的补测项保留为 `not_run` 或 `candidate`。

## 质量门禁

任一门禁失败时，必须修复报告、补证据或降级结论，不得发布未修正的 `confirmed`。

1. 未读取 TXT 或用户提供的项目输入，不得生成最终报告。
2. 未建立 TXT 到 Skill 映射，不得交付 Skill。
3. 未区分原文复刻和工程化补强，不得交付 Skill。
4. 未确认目标是本地授权环境，不得执行动态验证。
5. 未生成访问控制暴露面矩阵，不得进入动态验证结论。
6. 未创建或确认五类账号，不得声称完成角色矩阵。
7. 未创建或确认双租户测试资源，不得判定跨租户问题。
8. 未保存资源归属证明，不得标记 `confirmed`。
9. 未保存 request 和 response，不得标记 `confirmed`。
10. 只有 200 空响应、前端隐藏按钮、报错差异、管理员正常权限、本地测试数据错误，不得标记 `confirmed`。
11. path、query、body、form-data、header、cookie、GraphQL variable、WebSocket payload 未检查时，必须标记 `not_run`，不得省略。
12. 旧接口、移动端、admin/internal、自动 CRUD、批量、文件、缓存、异步任务、状态流未检查时，必须在非常规路径表记录。
13. 修改类验证没有 before、after、rollback 证据时，不得标记为已验证。
14. 输出缺少模板、checklist、examples、tests、失败处理或证据路径时，不得交付。
15. Skill 数量无理由超过 1 个，或存在空壳文件时，不得交付。

## 幻觉控制

1. 不编造请求、响应、文件路径、行号、账号、资源 ID、数据库记录、日志、截图、HAR。
2. 不把未执行命令写成已执行。
3. 不把静态可疑写成 `confirmed`。
4. 不把工具失败写成目标安全。
5. 不把管理员设计允许访问写成漏洞。
6. 不把 UUID 难猜写成安全控制；也不做暴力枚举。
7. 不使用真实用户隐私数据作为证明，只使用测试资源和 marker 内容。
8. 不访问外部目标；发现 base URL 非本地且未明确授权时停止。
9. 不省略失败原因；任何 `not_run`、`blocked`、`failed` 都必须写原因。
10. 不把工程化补强写成 TXT 原文。

## 失败处理

| 失败场景 | 处理 |
|---|---|
| `project_path` 不存在 | 停止执行，输出缺失输入报告 |
| `local_base_url` 无法访问 | 完成暴露面建模；动态项标记 `blocked` |
| 目标不是本地授权环境 | 停止动态验证；不生成漏洞结论 |
| 测试账号缺失 | 对缺失账号相关矩阵标记 `not_run` |
| 测试资源缺失 | 先在本地 fixture 中创建；不能创建则标记 `not_run` |
| 无回滚方式 | 只做只读验证；写操作、删除、状态变更标记 `blocked` |
| 无资源归属证明 | 相关结论不得为 `confirmed` |
| 请求重放失败 | 保存失败请求与错误，归为 `candidate` 或 `blocked` |
| 证据目录不可写 | 停止 `confirmed` 判断 |
| 动态结果不一致 | 保留全部证据，降级 `candidate`，写复测条件 |
| 修复后未验证 | 修复状态写 `unverified`；不得声称已修复 |

## 输出格式

最终报告必须使用 `templates/output-template.md`。关键结构如下：运行边界、项目识别结果、访问控制暴露面矩阵、测试身份、测试资源与归属证明、真实请求清单、动态验证结果摘要、confirmed、blocked、candidate、false_positive、反向审计回答、遗漏路径清单、非常规路径补测结果、修复优先级、回归测试脚本、结论限制。

## 自检清单

- [ ] 是否只在本地授权测试环境执行。
- [ ] 是否未访问公网第三方资产。
- [ ] 是否未读取真实用户隐私数据。
- [ ] 是否未破坏数据库或删除业务数据。
- [ ] 是否生成访问控制暴露面矩阵。
- [ ] 是否确认五类测试身份。
- [ ] 是否确认双租户测试资源与归属证明。
- [ ] 是否优先使用真实请求验证。
- [ ] 是否对每个候选问题完成正向、反向、越界尝试、阻断验证。
- [ ] 是否没有把静态猜测写成 `confirmed`。
- [ ] 是否没有把 200 空响应写成 `confirmed`。
- [ ] 是否没有把管理员正常权限写成漏洞。
- [ ] 是否所有 `confirmed` 都有请求、响应、账号、资源归属、根因、修复、回归验证。
- [ ] 是否逐条回答 15 个反向审计问题。
- [ ] 是否生成遗漏路径清单。
- [ ] 是否对非常规路径给出真实执行状态。
- [ ] 是否所有 `not_run`、`blocked`、`failed` 都写了原因。

## TXT 到 Skill 映射说明

| TXT 原文位置/标题 | Skill 文件 | 转化方式 | 原文复刻/工程化补强 | 备注 |
|---|---|---|---|---|
| 开头边界声明 | `SKILL.md` 适用范围、不适用范围、原文复刻规则、幻觉控制 | 转为启动条件、禁止条件、停止条件 | 原文复刻 | 保留本地授权、禁止公网、禁止真实隐私、可回滚要求 |
| 任务目标 | `SKILL.md` 适用范围、核心工作流 | 转为 Skill 目标和执行顺序 | 原文复刻 | 保留动态验证和对象归属缺陷范围 |
| 一、先做项目暴露面建模 | `SKILL.md` 阶段 1、`templates/output-template.md` | 转为暴露面矩阵字段 | 原文复刻 | 保留后端、前端、模型、权限、参数、框架默认行为 |
| 二、搭建最小动态验证环境 | `SKILL.md` 输入要求、阶段 2、`templates/output-template.md` | 转为测试账号、测试资源、归属证明字段 | 原文复刻 | 保留五类账号与双租户资源 |
| 三、动态验证方法 | `SKILL.md` 阶段 3-4、`examples/` | 转为请求提取和验证矩阵 | 原文复刻 | 保留 10 类动态验证方法 |
| 正向/反向/越界/阻断 | `SKILL.md` 阶段 4、质量门禁、`examples/basic-example.md` | 转为 confirmed 判定标准 | 原文复刻 | 无越界成功不得 confirmed |
| 四、严禁误报规则 | `SKILL.md` 质量门禁、幻觉控制、`checklists/quality-gate.md` | 转为误报过滤门禁 | 原文复刻 | 保留 8 条不得 confirmed 情况 |
| 五、严重程度判断 | `SKILL.md` 原文复刻规则、`templates/output-template.md` | 转为 severity 字段规则 | 原文复刻 | 高影响只在满足原文条件时使用 |
| 六、需要重点挖掘的偏门路径 | `SKILL.md` 原文复刻规则、阶段 6、`checklists/quality-gate.md` | 转为非常规路径补测要求 | 原文复刻 | 保留 20 类偏门路径 |
| 七、输出要求 | `SKILL.md` 输出要求、`templates/output-template.md` | 转为报告结构和 confirmed 字段 | 原文复刻 | 保留四类结果和 confirmed 必填字段 |
| 八、执行纪律 | `SKILL.md` 幻觉控制、失败处理、`checklists/final-review.md` | 转为证据纪律和降级规则 | 原文复刻 | 保留 not_run、失败原因、candidate 降级 |
| “现在开始”8 步 | `SKILL.md` 核心工作流 | 转为阶段性执行顺序 | 原文复刻 | 保留读取结构到回归脚本 |
| 反向审计 15 问 | `SKILL.md` 阶段 6、`templates/output-template.md`、`checklists/final-review.md` | 转为反查表和交付前检查 | 原文复刻 | 保留逐条回答要求 |
| 遗漏路径清单字段 | `SKILL.md` 输出要求、`templates/output-template.md` | 转为固定表格 | 原文复刻 | 保留全部字段 |
| 非常规路径 15 项 | `SKILL.md` 原文复刻规则、`templates/output-template.md`、`examples/full-example.md` | 转为补测矩阵 | 原文复刻 | 保留真实执行结果要求 |
| `run_id`、证据命名、状态枚举、证据脱敏、before/after/rollback | `SKILL.md` 工程化补强规则 | 新增可追溯执行约束 | 工程化补强 | TXT 未规定文件命名，新增用于验收 |
| README、模板、清单、示例、测试 | `README.md`、`templates/`、`checklists/`、`examples/`、`tests/` | 新增 Skill 落地文件 | 工程化补强 | 用于让 Claude 可调用、可验收、可复查 |
