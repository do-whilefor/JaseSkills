# Local Auth Gate Audit

## 适用范围

本 Skill 用于本地授权开源项目的认证、会话、权限门禁、账号状态、接口访问控制一致性动态验证。

调用本 Skill 的条件：

1. 目标是用户本机代码仓库、本机运行环境、本地服务、测试账号、测试数据库、测试租户、测试资源。
2. 用户目标是验证认证与访问控制一致性，不是公网扫描或第三方真实系统测试。
3. 允许读取本地项目文件、启动本地服务、创建测试 fixture、执行非破坏性动态请求、输出 evidence 证据目录。
4. 允许生成可复跑测试脚本、findings、replay plan、回归测试清单。

## 不适用范围

遇到以下条件，必须停止对应动作，并把原因写入 `blocked`：

1. 目标包含公网、第三方真实系统、未授权系统、真实用户数据或生产数据库。
2. 用户要求网络嗅探、证书劫持、流量劫持、中间人攻击、钓鱼、社工。
3. 用户要求 DoS、压力测试、破坏性删除、不可回滚写入、修改真实业务数据。
4. 授权边界不清，无法确认目标属于本地授权范围。
5. 项目只能连接生产环境，且不能切换测试数据库、fixture、seed 数据或事务回滚模式。

## 输入要求

执行前必须收集或在仓库中查找以下输入。找不到时，不能编造；必须输出最小本地补齐方案并标记 `blocked` 或 `candidate`。

| 输入项 | 仓库内查找位置 | 输出字段 | 缺失处理 |
|---|---|---|---|
| 项目路径 | 用户给定路径、压缩包根目录、当前工作目录 | `project_root` | 无项目路径则停止动态验证 |
| 授权边界 | 用户说明、README、环境说明 | `scope` | 边界不清时只做文件级建模 |
| 启动命令 | README、docs、package.json、pyproject.toml、pom.xml、go.mod、Cargo.toml、Makefile、docker-compose、scripts | `start_command` | 输出最小启动补齐方案 |
| 本地服务地址 | 配置文件、日志、默认端口、启动输出 | `base_url` | 未确认本地地址不得发请求 |
| 测试数据库 | docker-compose、migration、seed、fixture、test config | `test_db_setup` | 无测试 DB 时不执行写操作 |
| 测试账号 | seed、fixture、测试用例、认证模块、README | `test_accounts` | 生成最小 seed 草案，不改业务逻辑 |
| 证据目录 | 默认 `evidence/` | `evidence_dir` | 自动创建或记录无法创建原因 |
| 技术栈 | 依赖文件、入口文件、框架配置 | `stack` | 只记录可验证信息 |

最低测试身份：

- `anonymous`：未登录用户。
- `user_a`：普通用户，`tenant_a`。
- `user_b`：普通用户，`tenant_b`。
- `manager_a`：`tenant_a` 管理员或中权限用户。
- `admin`：系统管理员。
- `disabled_user`：禁用或冻结用户。
- `unverified_user`：未验证邮箱用户。
- `expired_session_user`：用于测试过期或失效会话。

## 输出要求

每次执行必须输出或说明无法输出的原因：

```text
evidence/
  run-manifest.json
  routes.json
  auth_surface_matrix.md
  test_accounts.json
  replay_results.json
  findings.md
  har/
  traces/
  screenshots/
```

最终报告必须按以下 14 节组织：

1. 项目认证架构摘要。
2. 暴露面矩阵。
3. 动态验证环境。
4. 测试账号和角色矩阵。
5. 已验证安全通过项。
6. confirmed 高影响缺陷。
7. candidate 高风险线索。
8. false positive 排除项。
9. blocked 项及阻塞原因。
10. 小众/偏门路径专项结果。
11. 依赖与框架默认行为风险。
12. 修复建议。
13. 回归测试脚本。
14. 下一轮验证清单。

结论等级只允许：

```text
confirmed / candidate / blocked / false_positive / needs_review
```

## 原文复刻规则

本节是 TXT 原文要求转成的执行规则。不得弱化、删除或改成泛泛说明。

### 授权边界

1. 只分析当前本地项目、当前仓库、当前本地运行环境。
2. 不扫描公网，不访问第三方真实系统，不使用真实用户数据。
3. 不做中间人攻击类路线，不做网络嗅探、证书劫持、流量劫持、钓鱼、社工。
4. 不执行破坏性操作，不删除数据库，不修改真实业务数据，不做 DoS，不做压力测试。
5. 所有验证必须使用测试账号、测试租户、测试角色、测试订单、测试资源。
6. 所有写操作必须可回滚，优先使用测试数据库、事务、fixture、seed 数据。
7. 不能把猜测当结论；没有动态证据只能标记 `candidate`，不能标记 `confirmed`。
8. 缺少启动命令、测试账号、环境变量、数据库初始化脚本时，先在仓库中寻找；找不到就给出最小可执行补齐方案，不编造。

### 目标缺陷类型

必须围绕以下缺陷做动态验证：

- 未登录访问受保护资源。
- 登录态失效后仍可访问。
- 低权限账号访问高权限接口。
- 普通用户访问管理员接口。
- A 用户访问 B 用户资源。
- A 租户访问 B 租户资源。
- 禁用、冻结、删除、未验证邮箱账号仍可访问。
- 退出登录后旧 cookie、旧 token、旧 session 仍可使用。
- token 过期、刷新、吊销、轮换逻辑异常。
- 前端隐藏接口但后端未校验。
- 前端不暴露参数但后端接受参数导致权限变化。
- API、GraphQL、WebSocket、后台路由、文件接口、导出接口、异步任务接口、Webhook、OAuth/OIDC 回调、密码重置、邮箱绑定、邀请注册、审批流、订单状态流中的认证或门禁缺陷。
- Web 登录、API token、移动端接口、后台接口、CLI token、服务端内部接口之间的认证方式差异。
- 中间件顺序、路由匹配、默认 allow、异常 fallback、反向代理 header、调试模式、mock 模式、feature flag 导致的门禁失效。
- 语言、框架、依赖、插件、ORM、路由库、鉴权库、session 库、JWT/OAuth 库、GraphQL/WebSocket 库引入的认证边界问题。

### 必须保留的执行阶段

1. 项目画像与暴露面建模。
2. 动态测试环境准备。
3. 动态验证方法。
4. 本地无害的小众/偏门路径验证。
5. confirmed 证据标准。
6. 自动化实现要求。
7. 报告输出格式。
8. 反幻觉要求。
9. 误报追责。
10. 30 类非常规认证门禁测试计划。
11. 最终验收问答。

## 工程化补强规则

本节是为了让 Skill 可执行而新增的工程化补强，不属于 TXT 原文。输出报告时必须标明此类内容是补强，不得伪装为原文。

1. 执行前创建 `evidence/run-manifest.json`，记录项目路径、授权边界、启动命令、测试 DB、执行时间、工具限制。
2. 每条动态请求写入 `evidence/replay_results.json`，字段包括 `case_id`、`entry`、`account`、`sample_type`、`request`、`expected`、`actual`、`evidence_files`、`verdict`、`reason`。
3. 所有 confirmed 必须通过 confirmed 门禁；缺任一证据字段时自动降级为 `candidate` 或 `needs_review`。
4. 所有 blocked 必须写明缺失项、已查找位置、本地补齐方式、补齐后的第一条验证命令。
5. 所有测试脚本优先放入 `tests/security/`；如果项目已有安全测试目录，使用项目既有目录。
6. 发请求前必须确认 `base_url` 是 `localhost`、`127.0.0.1`、本机容器地址或用户明确授权的本地服务地址。
7. 写操作必须绑定测试数据并记录回滚方式；没有回滚方式时不执行写操作。
8. 服务无法启动时，可以生成暴露面矩阵、测试计划、脚本草案和 blocked 记录，但不得写 confirmed。
9. Playwright、HAR、trace、截图不是同时必需；confirmed 至少需要动态请求证据、正反对照、可复现脚本或 curl 之一。
10. 工具限制导致无法保存某类证据时，必须写明限制，并保存替代证据：测试输出、响应摘要、日志路径或复现命令。
11. Skill 再生成或维护时，必须重新读取 TXT、重新读取现有 Skills、建立 TXT 到 Skill 映射表；未读取的文件标记为“未验证，不得宣称已通过”。

## 核心工作流

### 0. 范围确认

输出：

```text
scope.allowed = true/false
scope.reason = ...
scope.local_targets = [...]
scope.forbidden_targets = [...]
```

通过标准：目标限定在本地授权环境，且不需要公网、第三方系统、真实用户数据、破坏性操作或中间人路线。

失败处理：`scope.allowed=false` 时只输出边界说明、blocked 原因和需要的本地授权输入。

### 1. 文件清单与项目画像

先输出将读取的文件清单，再读取项目文件。必须覆盖：

- README、docs、启动脚本、依赖文件、环境示例、docker-compose、Makefile、CI 配置。
- 入口文件、路由注册、middleware 链、认证模块、权限模块、session/token 模块。
- User、Role、Permission、Tenant、Org、Team、Session、Token、APIKey、Invite、ResetPassword、EmailBinding、OAuthAccount 等模型。
- HTTP 路由、GraphQL schema、WebSocket event、RPC handler、后台任务入口、文件上传下载入口、导入导出入口。
- 认证装饰器、中间件、guard、policy、interceptor、filter、resolver、hook。
- 前端路由、前端权限判断、隐藏菜单、隐藏按钮、隐藏接口、懒加载 JS、sourcemap、环境配置、API client 封装。
- 与认证、会话、权限、路由、序列化、模板、文件、GraphQL、WebSocket 有关的依赖。

输出：

```text
evidence/routes.json
evidence/auth_surface_matrix.md
```

### 2. 认证与门禁暴露面矩阵

每个入口必须填写：

| 字段 | 填写规则 |
|---|---|
| 入口名称 | 路由、事件、任务、文件接口或回调名称 |
| 文件路径 | 代码路径；未知写 `unknown` |
| 方法/事件 | GET/POST/GraphQL resolver/WebSocket event/worker job 等 |
| 是否需要登录 | 是、否、needs_review |
| 需要的角色/权限/租户 | 角色、权限、tenant scope、owner scope |
| 代码中的校验位置 | middleware、guard、policy、resolver、service、query scope |
| 动态验证方式 | Playwright、测试框架、curl、GraphQL request、WebSocket client |
| 预期允许账号 | 从最低测试身份中选择 |
| 预期拒绝账号 | 从最低测试身份中选择 |
| 风险假设 | 可被验证的假设，不写结论 |
| 证据需求 | 状态码、响应字段、DB/log、HAR/trace/screenshot、测试输出 |

### 3. 动态测试环境准备

执行：

1. 找出启动命令。
2. 找出测试数据库或本地数据库初始化方式。
3. 找出 seed、fixture、测试账号创建方式。
4. 创建或识别最低测试身份。
5. 确认写操作回滚方式。
6. 启动本地服务或记录启动失败原因。
7. 保存 `evidence/test_accounts.json`；凭据、token、secret 只写占位符或本地引用路径。

### 4. 动态验证

对每个候选入口执行正向样本和反向样本。

正向样本：

- 合法账号访问合法资源应成功。
- 合法管理员访问管理接口应成功。
- 合法租户用户访问本租户资源应成功。

反向样本：

- `anonymous` 访问受保护接口应失败。
- `user_a` 访问 `user_b` 私有资源应失败。
- `tenant_a` 访问 `tenant_b` 资源应失败。
- 普通用户访问管理员接口应失败。
- `disabled_user` 访问核心接口应失败。
- `unverified_user` 访问要求验证邮箱的接口应失败。
- logout 后复用旧凭据应失败。
- 过期 token、被吊销 token、篡改 claims、缺失 claims、替换 user_id/tenant_id/role 参数应失败。
- 前端隐藏参数、后端接受参数、批量操作参数、嵌套 JSON 参数、GraphQL variables、WebSocket payload 中的身份字段必须测试。

每个失败预期必须记录实际状态码、响应体、数据库变化、服务端日志、截图或 trace。没有动态请求证据时不得写 confirmed。

### 5. 小众/偏门路径专项验证

必须验证项目实际存在的以下入口；不存在时记录为 `not_applicable`，不得删除该类检查：

1. 路由顺序：`/admin/:id`、`/:id`、`/api/*`、fallback route、catch-all route。
2. 中间件遗漏：同一资源的 list/detail/update/delete/export/import。
3. 方法差异：GET/POST/PUT/PATCH/DELETE/OPTIONS/HEAD。
4. 内容类型差异：application/json、form-data、x-www-form-urlencoded、text/plain、GraphQL variables。
5. 参数来源差异：path、query、body、header、cookie、session 中的 user_id、tenant_id、role、org_id。
6. 批量接口：ids、items、filters、where、include、expand、fields、sort、ownerId、tenantId。
7. 软删除和状态机：deleted、disabled、pending、draft、archived、approved、rejected、cancelled、expired。
8. 邀请与重置：invite token、reset token、email bind token、OAuth bind token。
9. 多租户隔离：tenant_id 是否来自客户端，查询是否缺少 tenant scope。
10. 本地缓存：应用缓存、服务端缓存中用户 A 的结果是否可能返回给用户 B。
11. 异步任务：导出、报表、队列、worker、webhook、定时任务是否只在提交时校验。
12. 文件资源：上传、下载、预览、导出、头像、附件、临时文件、私有文件 URL。
13. GraphQL：resolver、nested resolver、fragment、alias、batch query、introspection。
14. WebSocket：连接校验、消息处理校验、订阅 channel/room/tenant/user_id。
15. 依赖默认行为：框架、认证库、路由库、session/JWT/OAuth/GraphQL/WebSocket 库默认配置。

### 6. 误报追责

对每个已有 `confirmed` 逐条检查：

1. 是否有真实动态请求证据。
2. 是否有正向成功样本和反向失败预期样本。
3. 是否有异常成功结果，而不是代码推测。
4. 是否有测试账号、测试资源、测试租户、状态码、响应体、日志或数据库证据。
5. 是否有 Playwright trace、HAR、截图、curl、测试用例之一。
6. 是否验证未登录、普通用户、管理员、跨用户、跨租户、禁用用户、未验证用户、退出后旧凭据、过期 token。
7. 是否覆盖 REST、GraphQL、WebSocket、文件下载、导出、异步任务、Webhook、邀请、重置密码、邮箱绑定、OAuth 绑定。
8. 是否检查前端隐藏接口和后端实际接受参数。
9. 是否测试 body/query/path/header/cookie/session 中身份字段优先级。
10. 是否测试批量接口、嵌套对象、filter/where/include/expand/fields。
11. 是否因为接口返回 200 就误判为缺陷，而没有确认返回内容是否敏感、是否产生越权效果。
12. 是否因为接口返回 403 就停止，而没有检查同资源其他方法、路径、content-type。
13. 是否把无法复现的线索写成 confirmed。
14. 是否漏掉框架默认路由、fallback、catch-all、静态资源、调试接口。
15. 是否漏掉中间件顺序、装饰器继承、controller 级和 method 级权限覆盖。

处理规则：

- 删除所有证据不足的 confirmed。
- 把证据不足项降级为 candidate。
- 为每个 candidate 生成最小动态复现实验。
- 为每个 blocked 项说明缺什么，并给出本地补齐方式。
- 输出新的 findings.md、replay plan、回归测试脚本清单。

### 7. 30 类非常规认证门禁测试

每类都必须输出：测试入口、测试账号、正向样本、反向样本、请求构造、预期结果、实际结果、证据文件、结论等级、修复建议。

1. 路由混淆：尾斜杠、大小写、URL 编码、重复斜杠、路径参数为空、后缀格式、locale 前缀、版本前缀。
2. 方法覆盖：X-HTTP-Method-Override、_method 参数、框架 method fallback。
3. 内容解析差异：JSON、form、multipart、text/plain、空 body、重复 key、数组 key、嵌套对象。
4. 参数污染：query/body 同名参数、path/body 同名参数、header/body 同名参数。
5. 默认值风险：缺少 tenant_id、owner_id、role 时是否默认管理员、当前用户、首个租户或全局范围。
6. ORM 查询风险：where/filter/include/expand/select/order/group 是否允许客户端影响权限范围。
7. 批处理风险：批量 ids 中混入其他用户资源，部分成功是否泄露。
8. 导出风险：导出任务创建时校验和下载时校验是否一致。
9. 临时链接风险：预签名 URL、本地临时文件、附件 token 是否绑定用户、租户、过期时间。
10. 缓存风险：本地应用缓存是否按用户、租户、权限隔离。
11. 状态流风险：草稿、待审批、已取消、已删除、已归档资源是否可通过旧接口访问。
12. 邀请风险：邀请链接是否可跨邮箱、跨租户、重复使用。
13. 重置风险：密码重置后旧 session 是否失效，reset token 是否一次性。
14. 邮箱绑定风险：绑定 token 是否能绑定到错误账号。
15. OAuth 绑定风险：第三方账号绑定、解绑、重复绑定、回调 state 校验是否完整。
16. WebSocket 风险：连接后切换 room、tenant、user_id 是否重新校验。
17. GraphQL 风险：nested resolver、alias、fragment、batch query 是否绕过字段级权限。
18. 管理后台风险：菜单隐藏但接口可访问，前端按钮禁用但接口接受请求。
19. 错误处理风险：认证模块异常时是否 fallback allow。
20. 测试/开发配置风险：dev mode、mock auth、debug user、seed admin 是否在默认启动时启用。
21. 依赖升级风险：认证库、session 库、JWT 库、路由库历史默认行为是否与当前代码假设冲突。
22. 多入口风险：Web、API、移动端、后台、CLI、worker、webhook 是否共用一致的权限判断。
23. 旧接口风险：v1/v2、deprecated、legacy、compat route 是否缺少新权限逻辑。
24. 异步 worker 风险：任务入队时校验，执行时是否重新校验资源归属。
25. 审计日志风险：越权操作是否完全无日志，导致检测困难。
26. ID 生成风险：自增 ID、短 ID、可枚举 ID 是否扩大门禁缺陷影响。
27. 文件预览风险：缩略图、转码文件、缓存副本是否绕开原文件权限。
28. 软删除风险：deleted_at 资源是否仍可 detail/export/download。
29. 角色变更风险：降权后旧 session 是否仍保留旧权限。
30. 租户切换风险：同账号多租户切换后是否还能访问上一租户缓存或资源。

## 分阶段执行步骤

### 阶段 A：输出将读取的文件清单

```markdown
| 类别 | 路径/模式 | 目的 | 预期输出 |
|---|---|---|---|
| 启动说明 | README*, docs/* | 找启动命令和测试流程 | start_command |
| 依赖 | package.json / pyproject.toml / pom.xml / go.mod / Cargo.toml | 识别框架和认证依赖 | stack |
| 环境 | .env.example / config/* / docker-compose* | 找本地服务和测试 DB | test_db_setup |
| 路由 | src/**/routes*, app/**, controllers/** | 识别 HTTP 入口 | routes.json |
| 认证 | auth/**, middleware/**, guards/**, policies/** | 识别认证门禁 | auth_surface_matrix.md |
| 模型 | models/**, prisma/**, migrations/**, entities/** | 识别用户、角色、租户、token | test_accounts.json |
| 前端 | src/**, pages/**, router/**, api/** | 识别前端权限和隐藏接口 | auth_surface_matrix.md |
| 测试 | test/**, tests/**, fixtures/**, seed/** | 找测试账号和测试 DB | test_accounts.json |
```

### 阶段 B：生成暴露面矩阵

输出 `evidence/auth_surface_matrix.md`。动态验证前，所有风险只能是 `candidate`、`needs_review`、`blocked` 或 `not_applicable`。

### 阶段 C：启动本地服务

记录：

```text
start_command
base_url
db_mode
seed_mode
service_started: true/false
failure_reason
```

### 阶段 D：生成测试身份

识别或创建最低测试身份。凭据、token、secret 不写入报告，只写引用名和本地 secret 文件路径。

### 阶段 E：执行动态验证

按入口执行正反样本。每条写入 `evidence/replay_results.json`。

### 阶段 F：生成 findings.md

只把满足 confirmed 门禁的结果写入 confirmed。其余写入 candidate、blocked、false_positive 或 needs_review。

### 阶段 G：生成回归测试脚本清单

列出项目内可复跑脚本路径、命令、覆盖入口、预期结果、证据输出。

### 阶段 H：最终验收问答

必须回答：

1. 哪些认证门禁缺陷已经动态确认。
2. 哪些只是候选，为什么还不能确认。
3. 哪些路径没有覆盖，原因是什么。
4. 是否真实启动了服务并执行了请求。
5. 是否生成了可复跑测试。
6. 是否保留了 HAR、trace、截图、日志或测试输出。
7. 是否把所有 confirmed 都配了修复建议和回归测试。
8. 明天换一个审计人员，只根据 evidence/ 目录能否复现结论。

## 质量门禁

### Skill 交付门禁

用于维护或再生成本 Skill：

- [ ] 已重新读取原始 TXT。
- [ ] 已重新读取现有 Skills 全部文件。
- [ ] 未读取的文件已标记“未验证，不得宣称已通过”。
- [ ] 已建立 TXT 到 Skill 映射表。
- [ ] 已区分原文复刻和工程化补强。
- [ ] 未覆盖关键章节时不得通过。
- [ ] 未提供模板、checklist、examples、tests 时不得通过。
- [ ] 文件命名不能对应 TXT 核心主题时不得通过。
- [ ] Skill 数量无理由超过 1 个时不得通过。
- [ ] 空壳目录或空壳文件存在时不得通过。
- [ ] 输出不能追溯 TXT 时不得通过。

### confirmed 门禁

一个结果只有同时满足以下条件，才能标记为 `confirmed`：

- [ ] 动态请求已经执行。
- [ ] 有正向成功样本。
- [ ] 有反向失败预期样本。
- [ ] 实际结果出现异常成功或越权效果。
- [ ] 有测试账号、测试资源、测试租户。
- [ ] 有状态码和响应关键字段。
- [ ] 有数据库变化、日志证据、测试输出、HAR、trace、截图、curl 或测试用例之一。
- [ ] 能说明为什么这是认证或门禁缺陷，而不是测试误差。
- [ ] 有最小修复建议。
- [ ] 有修复后的 negative test。
- [ ] 有严重性判断依据。
- [ ] 标明是否跨用户、跨角色、跨租户、跨状态、跨认证方式。

缺任一项时，降级为 `candidate` 或 `needs_review`。

### candidate 门禁

- [ ] 有风险假设。
- [ ] 有受影响入口。
- [ ] 有需要的测试账号。
- [ ] 有最小动态复现实验。
- [ ] 写明还缺的证据。
- [ ] 写明不能确认为 confirmed 的原因。

### blocked 门禁

- [ ] 有阻塞项。
- [ ] 有已查找的位置。
- [ ] 有缺失输入或环境。
- [ ] 有本地补齐方式。
- [ ] 有补齐后的第一条验证命令。

### false_positive 门禁

- [ ] 有原风险假设。
- [ ] 有正反测试结果。
- [ ] 有排除依据。
- [ ] 有证据文件。

## 幻觉控制

执行时持续自问并写入最终验收：

- 是否真的启动了服务。
- 是否真的登录了不同角色。
- 是否真的发出了请求。
- 是否真的拿到了响应。
- 是否把失败预期和实际成功做了对照。
- 是否检查了数据库或日志。
- 是否有 trace、HAR、截图或测试输出。
- 是否把 candidate 错写成 confirmed。
- 是否只看前端权限而忽略后端接受性。
- 是否漏掉 GraphQL、WebSocket、异步任务、文件资源、导出接口。
- 是否漏掉多租户、禁用用户、未验证用户、退出后旧凭据、过期 token。
- 是否忽略依赖和框架默认行为。

禁止写法：

- “代码看起来有问题”不能作为 confirmed。
- “未看到权限判断”不能作为 confirmed。
- “接口返回 200”不能单独作为 confirmed。
- “前端隐藏按钮”不能单独作为 confirmed。
- 工具失败不能被隐藏，必须写入 blocked 或 needs_review。
- 无法复现不能写 confirmed。

## 失败处理

| 失败情况 | 处理动作 | 允许结论 |
|---|---|---|
| 未找到启动命令 | 查 README、脚本、配置；输出最小启动补齐方案 | blocked / candidate |
| 服务无法启动 | 保存错误日志、依赖缺口、补齐步骤 | blocked |
| 无测试账号 | 查 seed/fixture/test；生成最小测试 seed 草案 | blocked / candidate |
| 无测试数据库 | 只生成 fixture 和脚本草案，不执行写操作 | blocked |
| Playwright 不可用 | 使用项目测试框架、curl、requests、httpx、supertest 或 REST client | 由证据决定 |
| 无法保存 HAR/trace | 保存 curl、测试输出、响应摘要、日志路径 | 由证据决定 |
| 反向样本返回 403 | 继续测同资源其他方法、路径、content-type | false_positive / needs_review |
| 反向样本返回 200 | 检查响应内容、权限效果、DB/log，不直接确认 | candidate / confirmed |
| 写操作不可回滚 | 不执行，改为测试计划 | blocked |
| 目标超出授权范围 | 停止相关动作 | blocked |

## 输出格式

### 暴露面矩阵

```markdown
| 入口名称 | 文件路径 | 方法/事件 | 是否需要登录 | 需要的角色/权限/租户 | 代码中的校验位置 | 动态验证方式 | 预期允许账号 | 预期拒绝账号 | 风险假设 | 证据需求 |
|---|---|---|---|---|---|---|---|---|---|---|
```

### replay_results.json 单条记录

```json
{
  "case_id": "AUTH-001",
  "entry": "GET /api/orders/:id",
  "account": "user_a",
  "tenant": "tenant_a",
  "sample_type": "negative",
  "request": {
    "method": "GET",
    "url": "http://127.0.0.1:3000/api/orders/order_b",
    "headers_ref": "evidence/redacted-headers/user_a.json",
    "body_ref": null
  },
  "expected": {
    "status": [401, 403, 404],
    "effect": "不得返回 user_b 或 tenant_b 私有资源"
  },
  "actual": {
    "status": null,
    "key_fields": {},
    "effect": "not_run"
  },
  "evidence_files": [],
  "verdict": "blocked",
  "reason": "服务未启动或测试资源缺失"
}
```

### finding 记录

```markdown
## AUTH-001：<缺陷名称>

- 结论等级：confirmed / candidate / blocked / false_positive / needs_review
- 影响范围：
- 受影响入口/文件/函数：
- 触发前置条件：
- 测试账号和测试资源：
- 正向请求与预期成功：
- 反向请求与实际结果：
- 状态码与响应关键字段：
- 数据库变化或日志证据：
- HAR/trace/截图/curl/测试用例：
- 为什么不是测试误差：
- 严重性判断依据：
- 跨用户/跨角色/跨租户/跨状态/跨认证方式：
- 最小修复建议：
- 修复后的 negative test：
- 仍缺证据：
```

## 自检清单

- [ ] 已确认目标只包含本地授权项目、本地仓库、本地服务和测试数据。
- [ ] 已输出将读取的文件清单。
- [ ] 已识别语言、框架、入口文件、启动方式。
- [ ] 已识别路由、middleware、认证模块、权限模块、session/token 模块。
- [ ] 已识别 User、Role、Permission、Tenant、Session、Token、Invite、ResetPassword 等模型或确认不存在。
- [ ] 已生成认证与门禁暴露面矩阵。
- [ ] 已找到或生成本地测试身份方案。
- [ ] 已真实启动服务，或把启动失败写入 blocked。
- [ ] 已执行正向和反向样本，或把未执行原因写入 blocked。
- [ ] 已记录状态码、响应字段、日志、DB 变化或测试输出。
- [ ] 已覆盖 REST、GraphQL、WebSocket、文件、导出、异步任务、Webhook、邀请、重置、邮箱绑定、OAuth 绑定中项目实际存在的入口。
- [ ] 已覆盖 30 类非常规认证门禁测试计划。
- [ ] 没有把静态推测写成 confirmed。
- [ ] 没有把 200/403 单独当作结论。
- [ ] 每个 confirmed 都有修复建议和回归测试。
- [ ] 每个 candidate 都有最小动态复现实验。
- [ ] 每个 blocked 都有本地补齐方式。
- [ ] findings.md 与 evidence/ 能让其他审计人员复现结论。

## TXT 到 Skill 映射说明

| TXT 原文位置/标题 | Skill 文件 | 转化方式 | 原文复刻/工程化补强 | 备注 |
|---|---|---|---|---|
| 开头角色与目标 | SKILL.md 适用范围、核心目标 | 转为调用条件和目标边界 | 原文复刻 | 保留本地授权和动态验证闭环 |
| 严格边界 1-8 | SKILL.md 不适用范围、授权边界、失败处理 | 转为 hard rules 和 blocked 规则 | 原文复刻 | 禁止事项未弱化 |
| 任务目标缺陷列表 | SKILL.md 目标缺陷类型 | 转为必须覆盖的缺陷类型 | 原文复刻 | 保留认证、会话、权限、租户、状态、前后端不一致 |
| 第一阶段 | SKILL.md 文件清单、项目画像、暴露面矩阵 | 转为阶段 A/B 和矩阵字段 | 原文复刻 | 保留 11 个矩阵字段 |
| 第二阶段 | SKILL.md 动态测试环境准备 | 转为阶段 C/D 和测试身份要求 | 原文复刻 | 保留 8 类身份 |
| 第三阶段 | SKILL.md 动态验证 | 转为正向/反向样本规则 | 原文复刻 | 保留状态码、响应体、DB、日志、截图/trace |
| 第四阶段 | SKILL.md 小众/偏门路径专项验证 | 转为 15 类专项验证 | 原文复刻 | 保留本地无害验证约束 |
| 第五阶段 | SKILL.md confirmed 门禁、finding 记录 | 转为 15 个证据字段 | 原文复刻 | 保留未达标不得 confirmed |
| 第六阶段 | SKILL.md 输出要求、自动化实现 | 转为 evidence 目录和测试脚本规则 | 原文复刻 | 保留 Playwright/API/GraphQL/WebSocket 选择 |
| 第七阶段 | SKILL.md 输出要求、output-template.md | 转为 14 节报告模板 | 原文复刻 | 保留原报告结构 |
| 第八阶段 | SKILL.md 幻觉控制、自检清单 | 转为持续自检 | 原文复刻 | 保留 candidate/confirmed 防误判 |
| 误报追责段 | SKILL.md 误报追责、final-review.md | 转为 confirmed 降级规则 | 原文复刻 | 保留 15 条反查 |
| 30 类非常规测试 | SKILL.md 30 类测试、output-template.md | 转为必须填写的测试计划表 | 原文复刻 | 保留每项输出字段 |
| 最终验收问答 | SKILL.md 阶段 H、output-template.md | 转为最终报告必答项 | 原文复刻 | 保留 8 个问题 |
| 可执行文件化 | README、templates、checklists、examples、tests | 文件化支撑落地 | 工程化补强 | 不伪装成原文 |
| Skill 再生成质量控制 | quality-gate.md、tests/skill-quality-tests.md | 增加复刻一致性测试 | 工程化补强 | 为防止摘要化和空壳化 |
