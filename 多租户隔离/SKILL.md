# Tenant Isolation Dynamic Validation

## 适用范围

本 Skill 用于本机、本地容器、本地测试数据库、本地授权开源项目的租户隔离暴露面分析与动态验证。目标是让 Claude 按固定证据链验证高危租户隔离漏洞，而不是输出静态审计摘要。

适用输入包括：本地项目路径、本地 API 地址、本地测试数据库、测试租户、测试账号、测试角色、测试 token/API key 的脱敏值、marker 资源、HAR/trace/log/screenshot 证据路径。

## 不适用范围

不得用于公网真实系统、第三方系统、未授权系统、DoS/DDoS/压力测试、破坏性删除、清库、清文件、中间人攻击、真实敏感数据读取、真实 secret/token/cookie/password/private key 输出。

如果目标不满足本地或授权边界，停止动态请求，只输出安全替代方案：本地复现环境搭建、测试账号矩阵、marker 设计、报告模板。

## 输入要求

执行前必须记录下表。缺失项不得编造，必须标记 `blocked` 或 `unknown`。

| 输入项 | 必填 | 合格记录 | 缺失处理 |
|---|---:|---|---|
| 原始 TXT 来源 | 是 | 文件名、路径或用户粘贴内容 | 未读取不得生成 Skill 或报告 |
| 项目路径 | 是 | 本地绝对路径或相对路径 | 标记 blocked |
| API 基础地址 | 是 | `http://127.0.0.1:<port>`、localhost、本地容器地址 | 先从日志/配置定位，仍缺失则 blocked |
| 测试数据库 | 是 | 本地测试库位置，连接信息脱敏 | 无测试库不得写 confirmed |
| 租户 A/B | 是 | tenant/org/workspace/team/project/account 等 ID 或名称 | 用正常流程创建或 blocked |
| 角色矩阵 | 是 | owner/admin/member/viewer/service token | 缺项写影响范围 |
| marker 资源 | 是 | A/B 对照 marker 与归属证明 | 无 marker 不做越权结论 |
| 认证材料 | 是 | 脱敏 token/cookie/API key | 不输出原文 |
| 用户边界 | 否 | 只读、禁止写入、禁止导出等 | 覆盖默认流程 |

## 输出要求

最终报告固定包含：项目租户隔离事实画像、暴露面总表、租户/角色/资源测试矩阵、动态验证执行记录、confirmed 漏洞列表、high/critical 重点漏洞详情、candidate 漏洞列表、同族漏洞拓展结果、未覆盖区域和原因、修复建议、回归测试用例、审计可靠性自评、第二轮反向审判复核、距离 A 级可信度差距。

所有输出必须脱敏。confirmed 漏洞不得使用“不确定”措辞；缺少动态证据的点必须标记 candidate。

## 原文复刻规则

本节直接承接 TXT 的核心规则，不得弱化。

### 1. 强制边界

- 只能测试本机、本地容器、本地测试数据库、本地授权项目。
- 禁止访问公网敏感地址，禁止测试第三方真实系统。
- 禁止 DoS、DDoS、压力破坏、删除数据库、破坏业务、破坏文件、清空数据。
- 所有验证必须使用测试账号、测试租户、测试 marker 数据。
- 所有写操作必须是可回滚、低影响、无害 marker 级验证。
- 不使用中间人攻击路线。
- 不把“代码看起来有问题”判定为 confirmed。
- confirmed 必须有动态证据：请求、响应、账号身份、租户身份、资源归属、正反对照、可复现步骤。
- 没有动态证据只能标记 candidate。
- 输出不得包含真实 secret、token、cookie、密码、私钥。

### 2. 项目事实画像

必须先读取并输出：项目语言、框架、运行方式、包管理器、入口文件；REST/GraphQL/RPC/WebSocket/admin/API/internal 路由；Session/JWT/OAuth/API Key/Service Token/CLI Token/Webhook Token；RBAC/ABAC/Policy/Middleware/Guard/Decorator/Interceptor/Hook；tenant/org/workspace/team/project/account/company/site/space/environment 等租户模型；子域名、路径、Header、Cookie、JWT claim、Session、数据库字段、body、query、前端状态等租户来源；tenant_id、独立 schema、独立数据库、ORM scope、Repository filter、SQL where、cache key、对象存储路径、搜索索引、队列表等隔离方式；JS bundle、sourcemap、隐藏 API、未暴露参数、调试接口、feature flag、GraphQL query、WebSocket event；后台任务、导入导出、文件下载、Webhook、邮件模板、通知、审计日志、搜索、报表、缓存、队列、定时任务。

事实画像字段固定为：项目启动方式、测试数据库位置、认证入口、租户模型、租户识别来源、关键授权中间件、高风险模块、高风险参数、高风险表/模型、高风险接口、暂时无法确认的点。

### 3. 动态测试租户矩阵

至少创建或识别：A_owner、A_admin、A_member、A_viewer、A_service_token、B_owner、B_admin、B_member、B_viewer、B_service_token。项目不支持 service token 时标记 `not-applicable`，不得删除该检查项。

每个租户必须创建唯一 marker，包括：TENANT_A_PRIVATE_DOC_MARKER、TENANT_B_PRIVATE_DOC_MARKER、TENANT_A_INVOICE_MARKER、TENANT_B_INVOICE_MARKER、TENANT_A_FILE_MARKER、TENANT_B_FILE_MARKER、TENANT_A_WEBHOOK_MARKER、TENANT_B_WEBHOOK_MARKER、TENANT_A_AUDIT_LOG_MARKER、TENANT_B_AUDIT_LOG_MARKER。

可扩展对象：空租户、禁用/欠费/暂停租户、邀请中用户、已移除成员、只读用户、外部协作者、支持人员/平台管理员、API Key 用户、OAuth 绑定用户。

### 4. 动态验证总规则

每个候选点执行四类测试：正向测试、反向测试、角色对照、租户对照。confirmed 必须同时满足：请求身份属于租户 A；被访问资源属于租户 B；响应返回 B 数据或完成对 B 资源的未授权状态改变；有正向样本和反向样本；有可复现请求；有响应证据；有资源归属证明；不是测试数据污染、管理员预期权限、公开资源、缓存误判。

### 5. 必须覆盖的 11 类路线

| 路线 | 必须检查 | 必须动态验证 |
|---|---|---|
| IDOR/BOLA | id、user_id、tenant_id、org_id、workspace_id、team_id、project_id、account_id、company_id、site_id、file_id、invoice_id、payment_id、report_id、webhook_id、api_key_id、integration_id、audit_log_id、export_id、import_id | A 拿 B 资源 ID；改 path/query/body/nested ID；A parent+B child；B parent+A child；确认后端是否只校验存在 |
| 后端接受前端未暴露参数 | tenant_id、org_id、workspace_id、account_id、role、owner_id、created_by、user_id、is_admin、permissions、scope、plan、status、billing_account_id、target_tenant、impersonate_user、include_archived、include_deleted、all_tenants | 在创建、更新、查询、导出、搜索、邀请、授权、绑定、Webhook、集成配置接口注入 |
| ORM/查询层 | Model scope、Repository filter、Raw SQL、Join、count/sum/search/export/report、pagination、include/preload/populate、soft delete/archive/trash | A 调 list/search/export/stat/detail/report，检查 B marker |
| GraphQL | node(id)、globalId/base64、connection edges、nested resolver、mutation input、subscription、introspection、dataloader cache、resolver tenant 校验 | A 用 B global ID、nested query、mutation、subscription 验证 |
| WebSocket/SSE | user_id 校验、channel 可猜、客户端 tenant_id、join room、广播、通知/评论/任务/审批/聊天/工单 | A 订阅 B channel；B 触发 marker 事件；A 发送事件观察 B |
| 文件/对象存储/导入导出 | 上传归属、下载、预签名 URL、路径、object key、thumbnail、preview、export、import、临时文件、静态映射、附件关联 | A 访问 B file/export/object key/preview；A 创建文件注入 B tenant_id |
| 搜索/报表/审计/通知 | 全局搜索、模糊搜索、高级筛选、后台搜索、报表、activity feed、audit log、notification、message inbox、comments、history、version diff、trash | A 搜索/筛选/查看 B marker、B 操作、B 历史版本 |
| 邀请/成员/角色/切换 | 邀请链接、接受邀请 tenant_id、移除后 token/session、多租户切换、默认租户覆盖、前端状态、role 更新 user_id、membership 混淆 | A 邀请 B；B 替换租户；移除后访问；切换租户重放；改 tenant/org/workspace |
| API Key/Service Token/Integration | key 租户绑定、service token 跨租户、integration 配置、webhook secret、OAuth connection、同步任务、background worker | A_service_token/API key/integration/webhook 访问或绑定 B marker |
| 缓存/队列/异步/批处理 | cache key、job payload、worker 权限、batch export、email/report/notification、idempotency key、rate limit key、lock key | A/B 交替请求；B export 后 A 取；A 用 B idempotency key；A 触发 job 处理 B |
| 管理后台/平台能力 | admin/superadmin/support/staff/impersonation、tenant admin 误开平台权限、admin API 只检查登录、billing/plan/license | A_admin 访问平台接口；A_owner 操作 B billing；普通用户调用隐藏 admin API |

### 6. 暴露面枚举表

必须输出：`| 模块 | 文件路径 | 路由/接口 | 方法 | 参数 | 认证方式 | 租户来源 | 授权检查位置 | 风险点 | 动态验证状态 |`。禁止只写“检查接口权限”。每行必须对应具体文件、接口、参数、账号或 blocked 原因。

### 7. confirmed 与 candidate 格式

confirmed 必须输出：漏洞编号、漏洞名称、严重等级、影响租户、影响角色、影响资源、资源归属证明、请求身份证明、正向请求、正向响应摘要、越权请求、越权响应摘要、为什么这是租户隔离漏洞、为什么不是预期权限、复现步骤、最小化 PoC、涉及文件、根因代码、修复建议、回归测试建议、证据文件路径。

candidate 必须输出：候选编号、候选名称、代码位置、怀疑原因、缺少什么动态证据、下一步验证请求、需要的账号/租户/marker、预期成功结果、预期阻断结果、不能确认的原因。

### 8. 严重性判定

Critical：A 可读取或修改 B 大量敏感数据；A 可操作 B 管理员、成员、账单、API Key、Webhook、集成、文件、导出；普通租户用户获得平台级/全局级/跨租户能力；API Key/Service Token 可跨租户访问核心数据。

High：A 可读取 B 单个敏感对象；A 可修改 B 非破坏性 marker 数据；搜索、报表、审计日志、通知、文件预览泄露 B marker；邀请、成员、角色、项目关系跨租户混淆。

Medium：暴露 B 非敏感元数据；数量统计、存在性判断、名称枚举泄露；需要较高权限但仍越过租户边界。

Low：仅错误信息、无敏感数据、无状态改变、无可靠利用路径。

### 9. 同族漏洞拓展

发现 confirmed 后必须追踪同 controller、service、repository、DTO/schema、同模型 list/detail/update/delete/export/search/import、同资源 REST/GraphQL/WebSocket/后台任务/文件接口、同授权中间件缺失路由、同 tenant_id 客户端信任、同 cache/job/storage key、同前端隐藏参数。

输出同族拓展结果和矩阵：`| 原漏洞 | 根因模式 | 同族文件 | 同族接口 | 动态验证请求 | 结果 | 严重性 | 证据 |`。

### 10. 反幻觉要求

没跑动态请求不写“已验证”；没看到响应证据不写“可读取”；没证明 B 资源归属不写“跨租户”；没证明 A 无权不写“越权”；不能因变量名或状态码判定漏洞；403 不能结束路线；不能只测 GET、UI、API、HTTP；必须检查 WebSocket、GraphQL、导入导出、后台任务、缓存、文件；不能把公开资源、共享资源、平台管理员预期权限误报为漏洞。

### 11. 第二轮反向审判

第一轮报告后必须复核：每个 confirmed 的 A 身份、B 归属、A 无授权、正向样本、反向样本、角色对照、租户对照、请求响应证据、公开/共享/管理员预期权限排除、同资源多入口；缺任一项降级 candidate。每个 candidate 必须说明未 confirmed 原因、缺账号/租户/marker/请求、最小确认请求、confirmed 响应、blocked 响应、其他入口。

必须逐项检查 30 个盲区和 15 类偏门思路。最后输出第一轮误报、漏测、证据不足、未覆盖高危入口、第二轮新增 confirmed、第二轮新增 candidate、仍未覆盖高风险区域、下一步最小动态验证清单、优先修复项、回归测试位置、A/B/C/D 可信度评级。非 A 必须列出差距。

## 工程化补强规则

本节是为了让 Skill 可执行而新增，不得在报告中说成 TXT 原文。

### 状态标签

统一使用：`not-started`、`blocked`、`candidate`、`blocked-by-control`、`confirmed`、`not-applicable`、`unsafe-scope`。

### 证据最小化

请求只保留方法、本地路径、脱敏认证头、marker/tenant/resource 字段。响应只保留状态码、marker、tenant、resource、role、是否状态改变。外部证据只记录 HAR/trace/log/screenshot 路径。

### 写操作控制

POST/PUT/PATCH/DELETE 只允许 marker 级低影响验证。DELETE 只能清理由本轮创建的 marker。无回滚方式时写操作 blocked，并给只读替代验证。

### 归属和身份标准

资源归属证明至少来自：B 账号创建响应、本地测试库记录、管理界面/API 归属字段、B 正向访问响应。请求身份证明至少来自：`/me`/`/profile`/`/session`/`whoami`、JWT claim 脱敏解析、本地测试库 session 记录、API key 管理界面/API。

### TXT 复刻工程门禁

生成或修改 Skill 时必须先读取 TXT；必须建立 TXT 到 Skill 映射；必须区分原文复刻和工程化补强；新增目录/文件必须有调用价值；未验证文件不得宣称已通过。

## 核心工作流

1. 读取 TXT 和项目输入。
2. 执行边界确认。
3. 建立项目事实画像。
4. 验证启动状态和测试数据库。
5. 建立租户、角色、service token、marker 矩阵。
6. 枚举暴露面到文件、接口、参数、认证、租户来源、授权检查位置。
7. 生成 candidate。
8. 对每个 candidate 执行正向、反向、角色对照、租户对照。
9. 按证据分流 confirmed、candidate、blocked-by-control、blocked、not-applicable。
10. 对 confirmed 输出完整证据链和严重性。
11. 对 confirmed 做同族拓展。
12. 输出第一轮报告。
13. 执行第二轮反向审判，降级证据不足项。
14. 输出可信度评级和距离 A 的差距。

## 分阶段执行步骤

### 阶段 0：边界确认

输入：项目路径、API 地址、数据库、授权说明、用户限制。输出：safe-scope/unsafe-scope/blocked。若存在公网、第三方、破坏性、MITM、真实敏感数据读取，停止动态请求。

### 阶段 1：事实画像

读取依赖文件、启动文件、路由、controller、resolver、channel、job、worker、middleware、policy、model、repository、migration、schema、seed、前端 API client、bundle、sourcemap、配置。输出固定事实画像。找不到证据写 unknown。

### 阶段 2：启动验证

执行本地启动或检查容器；访问 health、登录页、API 根路径；确认测试数据库、队列、缓存、worker。启动失败时定位依赖/env/DB/migration/端口/权限/构建/队列/缓存问题，给最小修复和替代动态验证，不写 confirmed。

### 阶段 3：矩阵建立

使用 seed 或正常流程创建 A/B 租户、角色、service token、marker。每个 marker 记录 ID、归属证明、创建账号、清理方式。

### 阶段 4：暴露面枚举

按 11 类路线填表。每行必须有文件路径、接口、方法、参数、认证方式、租户来源、授权检查位置、风险点、动态验证状态。

### 阶段 5：动态验证

每个 candidate 执行四类测试。反向请求返回 200 时必须检查 B marker 或 B 状态改变；返回 403/404 时继续检查其他方法、参数、入口。无法执行写 blocked 和下一条最小请求。

### 阶段 6：漏洞分流

满足全部 confirmed 条件才写 confirmed。缺任何证据写 candidate。被正确阻断写 blocked-by-control。

### 阶段 7：同族拓展

根据根因追踪同 controller/service/repository/DTO/model/接口族。已动态验证写 confirmed 或 blocked-by-control；未动态验证写 candidate。

### 阶段 8：第二轮反向审判

逐条复核 confirmed、candidate、30 个盲区、15 类偏门思路，输出第二轮结论和评级。

## 质量门禁

报告或 Skill 交付前必须通过：已读取 TXT；已建立映射表；已区分原文复刻和工程化补强；已覆盖关键章节；已提供模板、checklist、examples、tests；已定义失败处理；命名可对应 TXT 核心主题；Skill 数量有理由；无空壳文件；输出可追溯 TXT；confirmed 有完整证据链；candidate 未伪装成 confirmed；已脱敏；未覆盖项有原因和下一条最小请求。

具体 gate 见 `checklists/quality-gate.md`。任一 gate 不通过，必须修复；无法修复时标记 blocked 并写原因。

## 幻觉控制

- 未读取的文件写“未验证，不得宣称已通过”。
- 未执行的动态请求不得写“已验证”。
- 未看到响应证据不得写“可读取”。
- 未证明资源归属不得写“跨租户”。
- 未证明 A 无合法授权不得写“越权”。
- 工程化补强必须标注为补强。
- 示例和测试不得当成真实漏洞证据。
- 只允许在本地、容器、测试库、授权项目内执行请求。

## 失败处理

| 失败类型 | 处理动作 | 禁止动作 |
|---|---|---|
| 目标超边界 | 标记 unsafe-scope，停止请求，输出本地替代方案 | 继续测试 |
| 项目启动失败 | 记录命令和日志，定位类别，给最小修复和替代动态验证 | 直接退回静态 confirmed |
| 缺账号/租户/marker | 查 seed 或正常流程创建；仍缺失则 blocked | 编造矩阵 |
| 写操作受限 | 执行只读验证或可回滚创建；写 blocked 原因 | 破坏真实数据 |
| 证据不足 | 保持 candidate，给最小验证请求 | 升级 confirmed |
| 无该技术面 | 标记 not-applicable，说明证据 | 删除该检查项 |

## 输出格式

使用 `templates/output-template.md`。章节顺序不得删除。无结果写“本轮未发现”，未覆盖写原因。

## 自检清单

- [ ] 只保留 1 个主 Skill。
- [ ] 无空壳目录、空壳文件、重复 Skill。
- [ ] 目录名为小写短横线，能体现租户隔离动态验证主题。
- [ ] SKILL.md 包含适用范围、不适用范围、输入、输出、原文复刻、工程化补强、工作流、阶段步骤、质量门禁、幻觉控制、失败处理、输出格式、自检、映射表。
- [ ] 模板有可填写字段。
- [ ] checklist 可逐项验收。
- [ ] examples 贴近本地授权租户隔离动态验证。
- [ ] tests 能发现漏复刻、摘要化、无关扩展、命名失败、目录臃肿、缺输入输出、缺门禁、缺失败处理、缺映射、补强伪装原文。
- [ ] 所有文件可追溯到 TXT 原文或工程化补强理由。

## TXT 到 Skill 映射说明

| TXT 原文位置/标题 | Skill 文件 | 转化方式 | 类型 | 备注 |
|---|---|---|---|---|
| 角色设定与任务目标 | `SKILL.md` 适用范围、核心工作流 | 转为 Skill 任务边界和执行目标 | 原文复刻 | 保留本地授权、动态验证、租户隔离 |
| 一、强制边界 | `SKILL.md` 强制边界；`quality-gate.md` | 转为 hard rules 和 gate | 原文复刻 | 禁公网、禁破坏、禁 MITM、必须脱敏 |
| 二、项目事实画像 | `SKILL.md` 事实画像；`output-template.md` | 转为固定字段和来源证据表 | 原文复刻 | 保留语言、框架、路由、认证、授权、租户模型等 |
| 三、动态测试租户矩阵 | `SKILL.md` 矩阵规则；`output-template.md` | 转为 A/B 角色与 marker 表 | 原文复刻 | 保留 service token 和 marker 名称 |
| 四、动态验证总规则 | `SKILL.md` 动态验证总规则 | 转为四类测试和 confirmed 条件 | 原文复刻 | 正向、反向、角色、租户对照 |
| 五、11 类漏洞路线 | `SKILL.md` 11 类路线表；`final-review.md` | 转为检查项和动态请求要求 | 原文复刻 | 保留 IDOR、隐藏参数、ORM、GraphQL、WebSocket、文件、搜索、邀请、token、缓存、admin |
| 六、暴露面枚举表 | `output-template.md` 暴露面总表 | 转为报告必填表 | 原文复刻 | 保留全部列名 |
| 七、confirmed 证据格式 | `output-template.md` 漏洞详情 | 转为 confirmed 模板 | 原文复刻 | 保留所有字段 |
| 八、candidate 格式 | `output-template.md` candidate 列表 | 转为候选模板 | 原文复刻 | 保留缺证据和下一步请求 |
| 九、严重性判定 | `SKILL.md` 严重性判定 | 转为等级规则 | 原文复刻 | 不新增等级 |
| 十、同族漏洞拓展 | `SKILL.md` 同族拓展；`output-template.md` 矩阵 | 转为拓展流程和表格 | 原文复刻 | 保留 controller/service/repository/DTO/model/接口族 |
| 十一、反幻觉要求 | `SKILL.md` 幻觉控制；`quality-gate.md` | 转为禁止误报规则 | 原文复刻 | 未跑请求不得已验证 |
| 十二、最终输出结构 | `output-template.md` | 转为固定报告章节 | 原文复刻 | 增补第二轮复核以承接后半 TXT |
| 反向审判模式 | `final-review.md`；`output-template.md` | 转为 confirmed/candidate/盲区/偏门思路复核 | 原文复刻 | 缺证据降级 candidate |
| 30 个覆盖盲区 | `final-review.md`；`output-template.md` | 转为逐项表格 | 原文复刻 | 每项需证据、原因、最小请求 |
| 15 类偏门思路 | `final-review.md`；`output-template.md` | 转为拓展清单 | 原文复刻 | 保留父子错配、归属污染等 |
| 第二轮结论与评级 | `output-template.md`；`SKILL.md` | 转为 A/B/C/D 评级和差距 | 原文复刻 | 非 A 必须列差距 |
| 状态标签、证据最小化、写操作控制、归属标准 | `SKILL.md` 工程化补强 | 新增执行状态和证据标准 | 工程化补强 | 用于落地验收，不冒充原文 |
| README、模板、清单、示例、测试 | `README.md`、`templates/`、`checklists/`、`examples/`、`tests/` | 新增交付结构 | 工程化补强 | 用于调用、填写、验收、回归测试 |
