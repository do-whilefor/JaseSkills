# ssrf-canary-audit

## 适用范围

用于当前本地授权开源项目的 SSRF 动态验证审计。目标是基于真实运行的本地项目、真实请求链路、真实应用日志和本地可控 canary 服务，证明或排除“目标应用服务端是否会请求用户可控地址”。

只在同时满足以下条件时使用：

1. 项目已明确授权，且审计对象是当前本地项目。
2. 目标应用可在本机、测试容器网络或测试目录 marker 服务中运行。
3. 动态验证目标只允许是本机可控 canary、测试容器网络或测试目录 marker 服务。
4. 输出目标是可复现、可证明、可回滚的 SSRF 动态验证报告。
5. 所有 confirmed 结论都能由 canary 日志、应用服务端日志、请求样本、响应样本和代码调用链同时支撑。

## 不适用范围

下列情况不得使用本 Skill 输出 confirmed、高危或严重结论：

1. 未授权项目、真实公网敏感地址、云厂商 metadata、真实内网资产、公司内网、第三方服务、生产服务。
2. DoS、DDoS、爆破、端口扫描、批量内网探测、破坏数据库、删除数据、影响业务正常运行。
3. 中间人攻击类型验证。
4. 只有静态代码审计、只有关键词 grep、只有理论推测、只有错误提示、只有超时、只有 DNS 解析。
5. 只有 URL 参数、只有 HTTP client 依赖、只有前端请求、只有浏览器直接访问 canary。
6. canary 回连不是来自目标应用服务端，或无法排除浏览器、测试工具、redirector 自身请求。
7. 无法提供唯一 marker、应用日志、代码调用链、正例、反例、blocked case 和复现步骤。

## 输入要求

执行前必须建立输入记录。缺少必填项时，只输出“环境缺口”，不得输出漏洞结论。

| 输入项 | 必填 | 记录内容 | 缺失处理 |
|---|---:|---|---|
| project_root | 是 | 本地授权项目根目录绝对路径 | 停止动态验证，输出缺口 |
| authorization_scope | 是 | 授权边界：仅本地项目、本机 canary、测试容器网络、测试目录 marker 服务 | 未确认授权则停止 |
| app_start_command | 是 | 启动命令或启动文档位置 | 从 README、package、compose、Makefile、脚本目录查找；仍未知则停止 |
| app_base_url | 是 | 本地目标应用地址 | 未启动则停止动态验证 |
| canary_base_url | 是 | 本地 canary 地址 | 未建立 canary 则停止动态验证 |
| evidence_dir | 是 | 默认 `evidence/ssrf/` | 不存在则创建；无法写入则停止 |
| allowed_networks | 是 | 本机、测试容器网络、测试目录 marker 服务 | 出现真实公网或真实内网则停止相关测试 |
| prohibited_targets | 是 | 真实公网敏感地址、云 metadata、真实内网资产、公司内网、第三方服务、生产服务 | 出现即拒绝该测试 |
| test_accounts | 条件必填 | 匿名、普通用户、高权限用户、管理员、多租户 A/B | 项目不支持则写“不适用”；缺账号则列入盲区 |
| tenant_model | 条件必填 | 租户隔离模型、租户 A/B 触发与执行边界 | 未知则跨租户结论为 needs_review |
| app_logs | 是 | 应用服务端日志路径或采集方式 | 无法采集则不得 confirmed |
| worker_logs | 条件必填 | 队列、worker、定时任务、失败重试日志 | 涉及异步链路时缺失即降级 |

## 输出要求

最终报告必须按以下十五节输出，不得替换为泛化报告：

1. 项目 SSRF 暴露面总览
2. SSRF source → sink 数据流图
3. 动态验证环境说明
4. canary 服务说明
5. 候选点矩阵
6. 已确认漏洞列表
7. 被阻断的安全用例
8. 误报排除列表
9. 高危链路深挖结果
10. 跨角色 / 跨租户 SSRF 组合风险
11. 修复优先级
12. 可直接执行的回归测试计划
13. 证据文件索引
14. 仍未覆盖的盲区
15. 下一轮深挖路线

每个 confirmed SSRF 必须包含：漏洞标题、影响功能、入口路由、需要权限、触发参数、完整请求样本、canary marker 日志、应用服务端日志、调用链代码位置、为什么证明是服务端请求、正例、反例、blocked case、是否可跨角色/跨租户、风险等级、修复建议、最小补丁方向、回归测试用例、复现命令、证据文件路径。任一项缺失，结论降级为 candidate 或 needs_review。

## 原文复刻规则

以下规则是 TXT 原文要求转成的硬规则，执行时不得弱化。

### 硬边界

1. 只允许测试当前本地授权项目。
2. 只允许访问本机可控 canary 服务、测试容器网络、测试目录中的 marker 服务。
3. 禁止访问真实公网敏感地址、云厂商 metadata、真实内网资产、公司内网、第三方服务、生产服务。
4. 禁止 DoS、DDoS、爆破、端口扫描、批量内网探测、破坏数据库、删除数据、影响业务正常运行。
5. 不做中间人攻击类型验证。
6. 所有验证必须可回滚、低频率、可复现、可证明。
7. 未拿到服务端到 canary 的真实回连证据，不得把 SSRF 判定为 confirmed，只能标为 candidate 或 needs_review。

### 本地动态验证环境

1. 先阅读项目结构，识别语言、框架、入口、路由、任务队列、配置、依赖、HTTP 客户端库、文件处理库、图片处理库、PDF/HTML 渲染库、Webhook 相关模块。
2. 找到项目启动方式，启动本地服务。
3. 建立本地 canary 服务，至少记录：请求时间、请求路径、请求方法、请求头、请求体摘要、来源 IP、User-Agent、是否来自目标应用服务端、marker id。
4. 每个测试用例生成唯一 marker：`/ssrf-marker/<route>/<param>/<case-id>`。
5. 所有动态验证只打到 canary，不访问真实敏感地址。
6. 证据保存到 `evidence/ssrf/`：canary 日志、应用日志、请求样本、响应样本、触发路径、代码位置、复现步骤、正例与反例、风险解释、修复建议。

### 暴露面梳理

不得只 grep `url`。必须从业务语义、依赖、代码路径、数据流四个角度查找 SSRF 暴露面。

用户可控 URL 参数必须至少检查：`url`、`uri`、`link`、`callback`、`redirect`、`webhook`、`avatar`、`image`、`logo`、`icon`、`importUrl`、`feed`、`rss`、`target`、`endpoint`、`host`、`domain`、`proxy`、`next`、`return`、`source`、`fileUrl`、`downloadUrl`、`previewUrl`。

隐藏入口必须至少检查：前端未暴露但后端接受的参数、JSON body 嵌套 URL、GraphQL input、WebSocket 消息、multipart 表单字段、YAML/JSON/XML 外部引用、Markdown/HTML 远程资源、OpenGraph 抓取、图片代理、头像远程拉取、PDF 远程资源、webhook 测试按钮、OAuth/OIDC/SAML discovery URL、插件/模板/主题远程安装、RSS/Atom、Git/仓库导入、数据源连接测试、邮件模板预览、管理后台连接测试、异步任务队列 fetch。

依赖层必须至少检查：HTTP client、URL parser、redirect-following library、image fetcher、HTML/PDF renderer、XML parser、cloud SDK、webhook SDK、proxy middleware、SSR rendering、headless browser、file importer、archive extractor。

服务端请求 sink 必须至少检查：`fetch`、`axios/request/got/http/https`、`curl wrapper`、`urllib/requests/aiohttp`、`net/http`、`RestTemplate/WebClient/OkHttp`、`Guzzle/cURL`、`open-uri`、headless browser navigation、image/PDF/HTML renderer 资源加载、XML external entity fetch、cloud metadata client、webhook sender、background worker HTTP call。

候选点矩阵字段必须包括：编号、路由/入口/功能、用户可控参数、参数来源、代码文件、调用链、sink、是否服务端请求、是否跟随跳转、是否有协议限制、是否有 host/IP 限制、是否有 DNS 解析校验、是否存在解析差异风险、是否异步触发、是否需要登录、需要的角色、初始风险等级、动态验证计划、当前状态 candidate/confirmed/blocked/needs_review。

### 动态验证判定

1. 对每一个 candidate，必须构造本地 canary 验证。
2. 正例必须证明目标应用服务端请求本地 canary，canary 收到带 marker 的请求，应用响应、应用日志、canary 日志能对应同一个 case-id，并能排除浏览器直接请求。
3. 普通浏览器直接访问 canary 不计为 SSRF。
4. 前端校验触发但服务端未请求 canary，不计为 confirmed。
5. 参数被保存但未触发服务端请求，不计为 confirmed。
6. 只看到错误信息，不计为 confirmed。
7. 只有代码上可能 fetch，没有动态证据，不计为 confirmed。
8. 阻断例只使用本地受控阻断目标和非法 scheme 测试，确认是否被拒绝；不得访问真实 metadata 或真实内网服务。
9. 异步任务必须观察 worker 是否实际请求 canary，并记录任务 id、队列日志、worker 日志、canary 日志。
10. 多角色验证覆盖匿名用户、普通用户、高权限用户、管理员、多租户用户 A、多租户用户 B；项目不支持时记录为不适用。

### SSRF 变体覆盖

所有变体只能指向本地 canary 或本地测试网络。必须覆盖：直接 URL 请求、跳转链触发、协议限制绕过风险、DNS 解析风险、URL 规范化差异、重定向后安全检查缺失、后端接受前端未暴露参数、JSON/YAML/XML/GraphQL/multipart 嵌套 URL、Markdown/HTML/SVG/PDF/Office/RSS/XML 文件内容触发、headless browser/PDF renderer/HTML preview/邮件模板预览、Webhook/callback 新建/测试/重试/失败重放/签名失败、缓存与去重、超时与错误处理、SSRF 与水平越权/垂直越权/多租户隔离/保存型后台任务触发组合。

### 严重性判断

只有满足下列条件之一，才允许评为高危或严重：低权限用户可触发服务端请求到受控 canary；能绕过服务端 URL 限制并触发 canary；能通过跳转链触发服务端请求；能在异步 worker、管理员预览、后台任务中触发服务端请求；能跨租户影响请求触发；能访问测试网络中的 marker 服务；能造成敏感配置、内部接口、测试 marker 的可证明读取或探测且仅限本地测试环境；能通过 SSRF 影响业务状态且必须是测试数据并可回滚。

不得因为下列情况直接判高危：只有 URL 参数；只有代码中存在 HTTP client；只有前端发请求；只有错误提示；只有超时；只有 DNS 解析；只有理论推测；没有 canary 回连证据。

### 修复建议要求

修复建议不得只写“过滤 URL”。必须覆盖：只允许业务必要协议例如 http/https；禁止危险 scheme；解析后再校验；跳转后重新校验最终地址；DNS 解析结果校验；连接前校验最终 IP；防止 DNS rebinding；禁止访问本地、回环、链路本地、私有网段，除非业务明确允许且有专用代理隔离；禁止用户直接控制完整 URL，改成服务端白名单资源 id；webhook 使用域名白名单、签名、限速、审计；图片代理/PDF 渲染/HTML 预览禁用远程资源或走隔离代理；异步任务记录触发用户、租户、目标地址、最终地址；多租户请求强制 tenant 绑定；增加单元测试、集成测试、动态回归测试。

### 结果反向审判

必须逐条反查每一个 candidate、confirmed、blocked、needs_review。对每一个 confirmed 回答：是否真的有 canary 回连；是否来自目标应用服务端；marker 是否唯一；请求时间是否对应；应用日志是否对应同一 case-id；是否存在前端直接请求误判；是否存在测试工具误判；是否存在 redirector 误判；是否有正例、反例、blocked case；是否有代码调用链；是否能复现；是否能用最小步骤复现；是否能写成回归测试。任一项缺失即降级。

### 补漏与最终追责

必须从“服务端会主动取资源”的角度重新审查，覆盖管理后台连接测试、Webhook 测试/重试/失败重放、头像远程导入、图片代理/缩略图、OpenGraph/link preview、RSS/Atom、Markdown/HTML/SVG 预览、PDF 生成、邮件模板预览、页面截图、headless browser、Git 仓库导入、第三方集成、OAuth/OIDC discovery、SAML metadata、插件/主题/模板远程安装、数据源连接器、对象存储自定义 endpoint、代理配置、任务队列延迟 URL、定时同步、失败重试、审批/通知/报表流、GraphQL mutation、WebSocket、multipart、YAML/JSON/XML 深层 URL、后端 DTO/model 隐藏字段、移动端 API、旧版 API、测试/debug/internal API。

最终追责审计必须逐条回答：是否只看显眼 URL 参数；是否漏 worker/队列/定时任务/失败重试；是否漏管理员预览/后台审核/系统任务；是否漏后端 DTO/model 隐藏字段；是否漏 GraphQL/WebSocket/multipart/导入文件；是否漏 redirect/DNS/URL 规范化/parser 差异；是否漏依赖库自动加载远程资源；是否只证明能提交 URL 而未证明服务端请求；是否把浏览器请求误判为服务端请求；是否缺少反例和 blocked case；是否缺少证据文件；是否缺少回归测试。

## 工程化补强规则

以下是为执行和验收新增的工程化规则，不得在报告中伪装成 TXT 原文。

1. case-id 统一为 `SSRF-YYYYMMDD-NNN-slug`。
2. 每个 case 使用独立目录：`evidence/ssrf/<case-id>/`。
3. 每个 case 至少保存：`request.http`、`response.txt`、`canary.log`、`app.log`、`code-chain.md`、`positive.md`、`negative.md`、`blocked.md`、`repro.md`、`regression.md`、`verdict.md`。
4. 状态只允许：candidate、confirmed、blocked、needs_review。
5. 严重性只允许：critical、high、medium、low、informational。
6. 没有 confirmed 不得使用 critical 或 high。
7. 每个入口记录触发者角色和执行者角色。
8. 每个动态用例默认单次、低频触发；禁止循环、并发、范围探测。
9. 项目启动失败、canary 无日志、来源不能归因、反例缺失、blocked case 缺失、代码链缺失、越界目标出现时，执行降级或停止，不得输出 confirmed。
10. 输出前必须运行 `checklists/quality-gate.md`、`checklists/final-review.md` 和 `tests/skill-quality-tests.md`。

## 核心工作流

1. 边界确认：核对授权范围、项目路径、本地测试网络、禁止目标。
2. 项目识别：读取项目结构、路由、任务队列、配置、依赖、HTTP 客户端、文件/图片/PDF/HTML/Webhook 模块。
3. 本地启动：启动目标服务，保存启动日志。
4. canary 建立：启动本地 canary，记录 marker、请求头、来源 IP、User-Agent、请求体摘要。
5. 暴露面矩阵：从业务语义、依赖、代码路径、数据流四个角度列出候选点。
6. source → sink 数据流：为每个候选点写明用户输入如何到达服务端请求 sink。
7. 动态验证：为 candidate 生成唯一 marker，只请求本地 canary 或测试 marker 服务。
8. 正例/反例/阻断：记录服务端请求证据、浏览器直连反例、本地阻断例。
9. 多角色/多租户：覆盖匿名、普通用户、高权限、管理员、租户 A/B；不支持时写明。
10. 变体覆盖：按直接请求、跳转、协议、DNS、规范化、隐藏字段、嵌套结构、文件内容、渲染、Webhook、缓存、错误处理、访问控制组合执行。
11. 证据归档：每个 case 单独目录保存请求、响应、日志、代码链、复现步骤。
12. 结果反向审判：逐条检查 confirmed 的证据字段；缺失即降级。
13. 最终追责审计：报告只保留有证据支撑的结论。
14. 回归测试：为 confirmed、blocked、needs_review 生成可执行回归计划。

## 分阶段执行步骤

### 阶段 0：授权与边界核验

核验对象：project_root、authorization_scope、allowed_networks、prohibited_targets、app_base_url、canary_base_url。

输出：`evidence/ssrf/_environment/scope.md`。

通过标准：授权明确；目标为本地项目；canary 为本机或测试网络；未出现真实公网敏感地址、云 metadata、真实内网、公司内网、第三方服务、生产服务。

失败处理：停止动态验证；输出环境缺口；不输出漏洞结论。

### 阶段 1：环境建立

执行步骤：定位启动方式；启动本地应用；保存应用启动日志；建立 canary；生成浏览器或 curl 直接访问 canary 的 baseline 反例；记录 canary 字段完整性。

输出：`evidence/ssrf/_environment/environment.md`、`app-start.log`、`canary-baseline.log`。

通过标准：目标应用可访问；canary 可记录请求；baseline 被标记为非 SSRF。

失败处理：应用未启动或 canary 无日志时停止；不得进入 confirmed 判定。

### 阶段 2：暴露面矩阵

执行步骤：按用户可控参数、隐藏入口、依赖层、sink、业务语义、代码路径、数据流建立矩阵。

输出：候选点矩阵。

通过标准：矩阵字段完整；每个 candidate 有动态验证计划；未测入口为 needs_review。

失败处理：矩阵缺字段时不得进入最终报告；补齐后继续。

### 阶段 3：动态验证

执行步骤：为每个 candidate 创建 case-id 和 marker；构造只指向 canary 的请求；触发目标功能；保存请求、响应、canary 日志、应用日志；标记正例、反例、blocked case。

输出：`evidence/ssrf/<case-id>/`。

通过标准：同一 case-id 能在请求样本、应用日志、canary 日志和代码调用链中对应。

失败处理：canary 未回连则保持 candidate 或 needs_review；来源不能证明为服务端则降级；越界目标立即停止该 case。

### 阶段 4：变体与组合验证

执行步骤：只使用本地 canary 或测试网络覆盖跳转链、协议限制、DNS/URL 规范化、重定向后校验、隐藏字段、嵌套数据、文件内容、服务端渲染、Webhook、缓存/去重、超时/错误处理、访问控制组合。

输出：变体矩阵、组合风险表。

通过标准：每个变体有 marker、预期、实际、证据路径和状态。

失败处理：未覆盖项列入盲区，不得推断为 confirmed。

### 阶段 5：反向审判

执行步骤：逐条审判 confirmed、candidate、blocked、needs_review；confirmed 缺任一证据字段即降级；记录降级原因和补测计划。

输出：降级列表、证据不足列表、新发现 candidate、confirmed、blocked、needs_review。

通过标准：报告中无证据不足的 confirmed。

失败处理：删除或降级无证据结论；补测计划按 P0/P1/P2 排序。

### 阶段 6：最终报告与回归

执行步骤：填充十五节报告；填充证据索引；生成修复优先级；生成可直接执行的回归测试计划；运行质量门禁、最终审查、质量测试。

输出：可上交级 SSRF 动态验证报告。

通过标准：confirmed 全部有 canary、应用日志、请求样本、代码链、正例、反例、blocked case、复现命令和回归测试。

失败处理：未通过门禁时不交付最终报告，只输出失败项和修复动作。

## 质量门禁

交付前必须全部通过：

1. 未读取 TXT 原文，不得生成 Skill 或报告。
2. 未建立 TXT 到 Skill 映射，不得通过。
3. 未区分原文复刻和工程化补强，不得通过。
4. 未覆盖硬边界、动态环境、暴露面、动态验证、变体、严重性、证据链、修复建议、反向审判、最终追责，不得通过。
5. 未提供模板、checklist、examples、tests，不得通过。
6. 未定义输入、输出、失败处理，不得通过。
7. 文件命名不能对应 SSRF canary audit 主题，不得通过。
8. 存在空壳文件、重复文件或无调用价值目录，不得通过。
9. 输出不可追溯 TXT 和证据文件，不得通过。
10. candidate 被写成 confirmed，不得通过。
11. 浏览器请求、测试工具请求、redirector 自身请求被写成服务端 SSRF，不得通过。
12. confirmed 缺 canary、应用日志、请求样本、代码链、正例、反例、blocked case、复现步骤、回归测试任一项，不得通过。
13. 修复建议只写“过滤 URL”，不得通过。
14. 回归测试不可执行，不得通过。

## 幻觉控制

1. 每条结论必须带证据路径；没有证据路径只能写 needs_review。
2. 不把推测写成事实；不把“可能 fetch”写成 confirmed。
3. 不把工程化补强写成 TXT 原文。
4. 不把未读取、未启动、未观察、未复现写成已完成。
5. 不把项目不支持的角色或租户覆盖写成已测；必须写“不适用”或“未覆盖”。
6. 不使用真实公网、真实内网、真实云 metadata 作为验证目标。
7. 所有补测计划必须包含 case-id、入口、角色、租户、参数、marker、触发步骤、预期 canary 行为、预期应用行为、反例、blocked case、成功/失败判定、证据路径。

## 失败处理

| 失败情况 | 处理动作 | 允许输出 |
|---|---|---|
| 授权范围不明确 | 停止动态验证 | 环境缺口 |
| 项目无法启动 | 停止动态验证 | 环境未就绪 |
| canary 无日志 | 停止 confirmed 判定 | needs_review |
| marker 不唯一 | 重建 case-id 与 marker | 不输出 confirmed |
| canary 回连来源不明 | 排除浏览器/工具/redirector；无法排除则降级 | candidate/needs_review |
| 缺应用服务端日志 | 降级 | candidate/needs_review |
| 缺代码调用链 | 降级 | candidate/needs_review |
| 缺正例 | 降级 | candidate/needs_review |
| 缺反例 | 降级 | candidate/needs_review |
| 缺 blocked case | 降级 | candidate/needs_review |
| 触发目标越界 | 停止该测试并记录违规输入 | 无漏洞结论 |
| 只有错误、超时、DNS、前端请求、URL 参数 | 不确认 | candidate/needs_review |
| 回归测试不可执行 | 不交付最终报告 | 修复任务 |

## 输出格式

使用 `templates/output-template.md`。所有表格中的空字段必须填写；无法填写时写明原因，并将相关结论降级或列入盲区。最终报告不得省略十五个主章节。

## 自检清单

- [ ] 只有一个主 Skill。
- [ ] 文件夹名为小写英文短横线，能对应 SSRF canary audit 主题。
- [ ] 所有文件有实际调用价值，无空壳文件。
- [ ] SKILL.md 包含适用范围、不适用范围、输入、输出、原文复刻、工程化补强、工作流、阶段步骤、质量门禁、幻觉控制、失败处理、输出格式、自检清单、TXT 映射说明。
- [ ] 模板字段可直接填写。
- [ ] checklist 可用于验收。
- [ ] examples 使用本地授权项目和本地 canary。
- [ ] tests 能发现漏复刻、摘要化、幻觉扩展、命名失败、目录臃肿、输入输出缺失、质量门禁缺失、失败处理缺失、映射缺失、补强伪装。
- [ ] confirmed 不缺任何强制证据。
- [ ] candidate、blocked、needs_review 未被夸大。
- [ ] 修复建议具体到协议、解析、跳转、DNS/IP、隔离代理、tenant、日志、回归测试。

## TXT 到 Skill 映射说明

| TXT 原文位置/标题 | Skill 位置 | 转化方式 | 类型 |
|---|---|---|---|
| 角色与目标 | 适用范围 | 转成使用条件和审计目标 | 原文复刻 |
| 硬边界 | 不适用范围、原文复刻规则、质量门禁 | 转成禁止事项、停止条件、降级规则 | 原文复刻 |
| 本地动态验证环境 | 输入要求、阶段 1 | 转成环境建立步骤与 canary 字段 | 原文复刻 |
| 第一阶段：暴露面梳理 | 暴露面梳理、阶段 2 | 转成参数/隐藏入口/依赖/sink/矩阵字段 | 原文复刻 |
| 第二阶段：动态验证 | 动态验证判定、阶段 3 | 转成正例、反例、blocked、异步、角色验证 | 原文复刻 |
| 第三阶段：SSRF 变体覆盖 | 变体覆盖、阶段 4 | 转成本地 canary 变体矩阵 | 原文复刻 |
| 第四阶段：严重性判断 | 严重性判断 | 转成高危允许条件和禁止高危条件 | 原文复刻 |
| 第五阶段：证据链要求 | 输出要求、阶段 5 | 转成 confirmed 强制字段 | 原文复刻 |
| 第六阶段：修复建议 | 修复建议要求 | 转成具体修复字段 | 原文复刻 |
| 第七阶段：最终输出格式 | 输出要求、输出格式 | 转成十五节报告模板 | 原文复刻 |
| 结果反向审判 | 反向审判、阶段 5 | 转成降级规则和证据反查 | 原文复刻 |
| 补漏、偏门、依赖反查、强制补测 | 补漏与最终追责、阶段 4-6 | 转成补测优先级和盲区机制 | 原文复刻 |
| case-id、证据文件名、严重性枚举、门禁运行顺序 | 工程化补强规则 | 转成可执行约束 | 工程化补强 |
