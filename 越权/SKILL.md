# authz-bypass-dynamic-audit

本 Skill 复刻《越权提示词转skills.txt》的执行意图：只在本机或授权开源项目中，对越权暴露面做项目画像、多角色/多租户动态验证、证据闭环、误报追责、漏测追责和非常规路径深挖。

本 Skill 不是漏洞知识摘要。调用时必须产出可验收文件、动态请求证据、结论分级和 TXT 映射。

## 适用范围

[原文复刻]

仅当目标满足以下全部条件时使用：

1. 目标是用户本机、用户授权的开源项目代码、本地启动的服务，或测试环境中创建的账号、租户、数据库、文件和资源。
2. 任务目标是“越权暴露面分析 + 多角色动态验证 + 证据闭环”。
3. 验证对象属于授权访问控制边界，包括水平越权、垂直越权、多租户隔离失效、IDOR、BOLA、BFLA、前端隐藏接口但后端未校验、前端隐藏参数但后端接受参数、批量接口越权、导出/下载/预览/附件/报表越权、GraphQL resolver 越权、WebSocket room/channel 越权、异步任务/队列/Webhook/回调越权、管理后台/内部/遗留/debug 接口越权、状态机越权、缓存/软删除/归档/草稿/历史版本越界访问，以及依赖、框架、ORM、路由库、权限库默认行为导致的门禁不一致。
4. 允许在本地启动服务、创建测试账号、创建测试租户、创建测试资源、发起本地动态请求并保存 evidence/ 证据文件。

## 不适用范围

[原文复刻]

出现任一条件时停止动态验证，并输出 blocked 或拒绝原因：

1. 目标是公网、第三方真实系统、未授权系统或授权边界不明的系统。
2. 需要扫描公网、攻击第三方真实系统、使用真实用户数据。
3. 需要中间人攻击、流量劫持、证书劫持、钓鱼或社工。
4. 需要 DoS、DDoS、压力破坏或批量爆破。
5. 需要删除数据库、破坏业务正常运行，或修改生产逻辑来制造漏洞。
6. 用户要求把静态猜测写成 confirmed。
7. 没有动态请求、正反对照和证据文件，却要求输出 confirmed。

## 输入要求

调用本 Skill 时必须先收集下列输入。缺失项不得编造，必须写入 blocked。

| 输入项 | 必填 | 验证动作 | 输出位置 | 缺失处理 |
|---|---:|---|---|---|
| 原始 TXT 或已确认的 TXT 文件名 | 是 | 确认使用《越权提示词转skills.txt》规则 | 最终报告“审计依据” | 未读取 TXT 不得执行 Skill 生成 |
| 项目路径 | 是 | 检查路径是否存在，列出顶层结构 | evidence/replay_plan.md | 无路径则 blocked |
| 授权范围 | 是 | 记录“本机/授权开源项目/测试环境”说明 | evidence/blocked.md 或报告元数据 | 不明确则只做静态画像，不做动态请求 |
| 本地 base URL | 否 | 从启动日志、env、docker compose、端口配置识别 | evidence/logs/startup.log | 找不到则 blocked |
| 启动命令 | 是 | 从 README、package.json、Makefile、docker-compose、pyproject、go.mod、pom.xml、Cargo.toml 查找 | evidence/replay_plan.md | 找不到则列候选命令并 blocked |
| 数据库初始化方式 | 是 | 查找 migration、seed、fixture、测试配置 | evidence/replay_plan.md | 找不到则写最小 fixture 计划 |
| 测试身份创建方式 | 是 | 查找注册、登录、测试工厂、seed | evidence/test_accounts.json | 缺失则 blocked 或写本地 fixture 方案 |
| 测试资源创建方式 | 是 | 查找创建资源、创建租户、创建角色流程 | evidence/test_resources.json | 缺失则 blocked 或写本地 fixture 方案 |
| 测试工具 | 是 | 识别 Playwright、curl、httpx、requests、supertest、pytest、Postman、GraphQL client、WebSocket client | evidence/replay_plan.md | 未发现则写可执行本地请求方式 |

## 输出要求

[原文复刻]

最终报告必须包含以下 13 个部分：

1. 项目越权风险架构摘要。
2. 越权暴露面矩阵。
3. 多角色 / 多租户测试矩阵。
4. 动态验证环境说明。
5. 已确认高影响越权问题。
6. 候选高风险线索。
7. 已排除误报。
8. 阻塞项和补齐办法。
9. 小众 / 偏门路径专项结果。
10. 依赖和框架默认行为风险。
11. 修复建议。
12. 回归测试清单。
13. 下一轮深挖计划。

必须生成或建议生成以下 evidence/ 目录：

```text
evidence/
  authz_surface_matrix.md
  test_accounts.json
  test_resources.json
  replay_plan.md
  replay_results.json
  findings.md
  false_positives.md
  blocked.md
  har/
  traces/
  screenshots/
  logs/
  curl/
  tests/
```

[工程化补强]

可额外生成 `evidence/_index.md` 作为证据索引。该文件不是 TXT 原文要求，不能把它列为 confirmed 的必要条件。

## 原文复刻规则

下列规则来自 TXT，执行时不得弱化：

1. 先完整读取项目结构，不得只看标题、README 或单个路由文件后下结论。
2. 项目画像必须识别：编程语言、框架、入口文件、启动命令、路由注册方式、controller、handler、resolver、service、middleware、guard、policy、decorator、interceptor。
3. 必须识别用户、角色、权限、租户、组织、团队、资源归属相关模型。
4. 必须识别权限判断函数、租户过滤函数、owner 校验函数。
5. 必须枚举所有 REST API。
6. 必须枚举所有 GraphQL schema、query、mutation、resolver；不存在时写“未发现 GraphQL 入口”。
7. 必须枚举所有 WebSocket event、room、channel、subscription；不存在时写“未发现 WebSocket 入口”。
8. 必须枚举文件上传、下载、预览、导出、导入接口。
9. 必须枚举后台任务、队列任务、定时任务、Webhook、OAuth 回调、邀请、重置密码、邮箱绑定流程。
10. 必须检查前端路由、懒加载 JS、API client、权限按钮、隐藏菜单、隐藏参数。
11. 必须检查 package、lockfile、依赖库中与路由、鉴权、会话、ORM、GraphQL、WebSocket、文件处理相关的部分。
12. 必须输出《越权暴露面矩阵》，字段为：入口名称、请求方法或事件名、路径 / resolver / handler、代码文件、资源类型、资源归属字段、预期访问角色、预期禁止角色、预期租户边界、权限校验位置、可能缺失的校验点、动态验证方法、正向样本、反向样本、证据需求、当前状态。
13. 第二阶段必须让项目真实跑起来，不能只做静态审计。
14. 如果没有测试数据，新增最小测试 fixture；不得修改业务安全逻辑。
15. 项目已有测试框架时优先复用项目测试框架。
16. Web 项目优先使用 Playwright 做真实浏览器流程。
17. API 项目优先使用项目内测试框架、curl、httpx、requests、supertest、pytest 或 Postman collection。
18. 有 GraphQL 时必须写 GraphQL 动态请求。
19. 有 WebSocket 时必须写 WebSocket 客户端动态验证。
20. 至少准备 anonymous、user_a、user_b、manager_a、manager_b、admin、disabled_user、readonly_user、unverified_user、role_changed_user。
21. 至少准备 user_a_resource、user_b_resource、tenant_a_private_resource、tenant_b_private_resource、tenant_a_file、tenant_b_file、tenant_a_export_job、tenant_b_export_job、pending_resource、approved_resource、deleted_resource、archived_resource、draft_resource。
22. 每一个入口都必须做正反对照。
23. 每次验证必须记录：请求账号、请求资源、请求方法、请求路径、请求参数、请求体、cookie/token 来源、状态码、响应关键字段、数据库变化、服务端日志、截图/HAR/trace/测试输出/curl 复现命令、预期结果、实际结果、是否构成越权。
24. 重点深挖 18 类路径：同资源不同接口、同接口不同方法、同接口不同 Content-Type、参数污染、客户端可控身份字段、批量操作、ORM 查询、GraphQL、WebSocket、文件资源、异步任务、状态机、角色变化、多入口差异、旧版本接口、fallback 路由、框架默认行为、前后端不一致。
25. 结论只能是 confirmed、candidate、blocked、false_positive、needs_review。
26. confirmed 必须有真实动态请求、正反样本、异常成功结果、证据文件、可复现步骤。
27. candidate 用于代码路径可疑但没有完整动态证据。
28. blocked 必须说明阻塞原因和补齐方法。
29. false_positive 必须说明为什么排除。
30. needs_review 用于证据不完整、影响判断不稳定、需要人工复核。
31. 严禁把 candidate 写成 confirmed。
32. 每一个 confirmed 越权问题必须在 findings.md 中包含：漏洞标题、类型、影响接口、影响文件、影响角色、影响租户、影响资源、触发条件、正向请求、反向请求、实际异常成功结果、状态码、响应关键字段、数据库或日志证据、HAR/trace/screenshot/curl/test output 路径、可复现步骤、最小修复建议、修复后的回归测试、严重性判断、结论等级。
33. 初步结论后必须切换成“越权动态验证审计官 / 误报追责官 / 漏测追责官”。
34. 没有动态证据的 confirmed 全部降级为 candidate。
35. 每个 candidate 必须生成最小动态复现计划。
36. 每个 blocked 必须说明缺少什么，并给出本地补齐方法。
37. 每个 false_positive 必须说明排除依据。
38. 每个 confirmed 必须配回归测试。
39. 必须重新生成 findings.md、replay_plan.md、authz_surface_matrix.md。
40. 必须执行或阻塞记录 50 项非常规测试方向，每项输出测试编号、测试入口、测试账号、测试资源、请求构造、预期结果、实际结果、证据文件、结论等级、修复建议。

## 工程化补强规则

以下规则不是 TXT 原文，但用于让 Skill 可执行、可验收、可追溯：

1. 所有 Skill 文件中的新增规则必须标注为“工程化补强”或在映射表中说明。
2. 可使用 `AUTHZ-YYYYMMDD-NNN` 作为本地 replay 编号；这是证据管理格式，不是漏洞成立条件。
3. 可生成 `evidence/_index.md` 索引证据；这是补强文件，不替代 TXT 要求的 evidence 文件。
4. 对每个入口执行最小样本集：一个正向样本、一个同用户/同租户合法样本、一个跨用户或跨租户反向样本；入口不适用时写明不适用原因。
5. 所有命令必须指向本地 URL、回环地址、容器网络名或用户明确授权的测试地址。
6. 自动化测试依赖随机数据时，必须写 seed、fixture 或清理步骤。
7. 修复建议必须指出校验位置、校验对象、校验条件、失败返回、回归测试，不输出只有口号的修复意见。
8. 任何文件无法读取时，在审查输出中写“未验证，不得宣称已通过”。

## 核心工作流

1. 读取 TXT 与调用输入，确认授权边界。
2. 创建 evidence/ 目录骨架。
3. 读取项目结构与依赖，建立项目画像。
4. 枚举 REST、GraphQL、WebSocket、文件、后台任务、前端 API client、旧接口和 fallback 入口。
5. 生成 authz_surface_matrix.md。
6. 启动本地服务并初始化测试数据库。
7. 创建或识别测试身份与测试资源。
8. 对每个入口执行正反对照动态请求。
9. 执行 18 类重点深挖与 50 项非常规测试。
10. 按证据分级写 findings、candidates、false positives、blocked。
11. 对 confirmed 逐条做 25 项误报追责。
12. 生成最终 13 部分报告。

## 分阶段执行步骤

### 阶段 0：TXT 与授权边界确认

执行动作：

1. 确认已读取《越权提示词转skills.txt》或用户提供的同等全文。
2. 记录项目路径、授权说明、本地 base URL、测试数据库说明。
3. 检查请求目标是否属于本机、授权开源项目、本地服务或测试环境。
4. 检查计划中是否包含公网扫描、第三方攻击、真实用户数据、劫持、钓鱼、社工、DoS、爆破、删除数据库、破坏业务或修改生产逻辑。

输出：

- `evidence/blocked.md`
- `evidence/replay_plan.md`

通过标准：

- TXT 已读取。
- 授权边界明确。
- 动态请求只指向授权本地范围。

失败处理：

- TXT 未读取：停止 Skill 生成或审计，输出“未验证，不得宣称已通过”。
- 授权不明确：只允许静态项目画像，所有动态请求标 blocked。
- 请求越界：删除越界请求并记录拒绝原因。

### 阶段 1：项目暴露面建模

分析对象：

- 项目根目录与启动文件。
- README、package、lockfile、docker-compose、Makefile、测试配置。
- 路由、controller、handler、resolver、service、middleware、guard、policy、decorator、interceptor。
- 用户、角色、权限、租户、组织、团队、资源归属模型。
- 权限判断、租户过滤、owner 校验函数。
- REST、GraphQL、WebSocket、文件接口、后台任务、Webhook、OAuth 回调、邀请、重置密码、邮箱绑定。
- 前端路由、懒加载 JS、API client、权限按钮、隐藏菜单、隐藏参数。

输出：

- `evidence/authz_surface_matrix.md`
- `evidence/replay_plan.md`

通过标准：

- 每个入口都有代码文件或 unknown。
- 每个资源入口都有资源归属字段或 unknown。
- 每个入口都有正向样本、反向样本和证据需求。

失败处理：

- 无法识别的字段写 unknown。
- 找不到权限校验位置时写 candidate，不写 confirmed。

### 阶段 2：动态验证环境准备

执行动作：

1. 找到本地启动命令。
2. 找到数据库初始化方式。
3. 找到测试数据 seed 或 fixture。
4. 找到登录、注册、创建资源、创建租户、创建角色流程。
5. 若无测试数据，新增最小 fixture，不改业务安全逻辑。
6. 复用项目测试框架；Web 用 Playwright；API 用项目测试框架、curl、httpx、requests、supertest、pytest 或 Postman collection。
7. GraphQL 写动态请求；WebSocket 写客户端动态验证。
8. 创建或识别必需测试身份和资源。

输出：

- `evidence/test_accounts.json`
- `evidence/test_resources.json`
- `evidence/logs/startup.log`
- `evidence/replay_plan.md`

通过标准：

- 服务真实启动。
- 测试账号和资源可用于正反对照。
- 缺失项有 blocked 原因和补齐方法。

失败处理：

- 启动失败：记录命令、日志、缺失依赖、补齐方法。
- 数据库失败：记录配置、migration/seed 错误、补齐方法。
- 账号或资源失败：记录失败接口、字段、替代 fixture 方案。

### 阶段 3：入口级正反对照动态验证

验证对象：`authz_surface_matrix.md` 中每个入口。

执行动作：

1. 用 user_a 访问自己的资源，验证应成功。
2. 用 user_b 访问自己的资源，验证应成功。
3. 用 manager_a 访问 tenant_a 管理范围，验证应成功。
4. 用 admin 访问管理接口，验证应成功。
5. 用合法租户用户访问本租户资源，验证应成功。
6. 用 anonymous 访问受保护资源，验证应失败。
7. 用 user_a 访问 user_b_resource，验证应失败。
8. 用 user_b 访问 user_a_resource，验证应失败。
9. 用 tenant_a 用户访问 tenant_b_private_resource，验证应失败。
10. 用 tenant_b 用户访问 tenant_a_private_resource，验证应失败。
11. 用普通用户访问管理员接口，验证应失败。
12. 用 readonly_user 执行写操作，验证应失败。
13. 用 disabled_user 访问核心资源，验证应失败。
14. 用 unverified_user 访问需要验证状态的接口，验证应失败。
15. 用 role_changed_user 的旧 session 访问高权限接口，验证应失败。
16. 验证删除、归档、草稿、待审批资源不得通过旧接口越权访问。
17. 验证批量接口混入其他用户或租户资源时失败或只返回合法部分。
18. 验证文件下载、预览、缩略图、导出文件重新校验归属。
19. 验证 GraphQL nested resolver 不泄露其他用户或租户数据。
20. 验证 WebSocket 连接后切换 room、tenant_id、user_id 不得越权订阅。

通过标准：

- confirmed 同时具备动态请求、正向样本、反向样本、异常成功结果、证据文件、可复现步骤。
- 200 状态码只有在响应字段、资源归属、数据库变化或业务状态变化证明越权效果时才可支撑 confirmed。

失败处理：

- 无动态请求：candidate。
- 无正反对照：candidate。
- 无证据文件：candidate。
- 访问被正确拒绝：false_positive。
- 影响不稳定：needs_review。
- 环境缺失：blocked。

### 阶段 4：重点深挖

必须覆盖或阻塞记录以下 18 类：

1. 同资源不同接口：list、detail、create、update、delete、export、import、download、preview、share、copy、archive、restore。
2. 同接口不同方法：GET、POST、PUT、PATCH、DELETE、HEAD、OPTIONS。
3. 同接口不同 Content-Type：application/json、form-data、x-www-form-urlencoded、text/plain、空 body、重复 key、数组 key、嵌套对象。
4. 参数污染：path、query、body、header、cookie、session 中同时出现 user_id、owner_id、tenant_id、role、org_id。
5. 客户端可控身份字段：user_id、account_id、member_id、tenant_id、org_id、team_id、role、permission、is_admin、owner_id、created_by、updated_by、assignee_id、approver_id。
6. 批量操作：ids、items、filters、where、include、expand、fields、select、sort、group、ownerId、tenantId。
7. ORM 查询：findMany、findFirst、findUnique、raw query、include、join、populate、preload。
8. GraphQL：query、mutation、nested resolver、alias、fragment、batch query、introspection、node/id、connection edges。
9. WebSocket：connect 与 message 校验、room、channel、tenant、user_id、resource_id。
10. 文件资源：原文件、缩略图、预览图、转码文件、临时文件、导出文件、附件 URL、缓存副本。
11. 异步任务：导出、报表、队列、Webhook、定时任务。
12. 状态机：草稿、待审批、已审批、已拒绝、已取消、已删除、已归档、已过期。
13. 角色变化：升权、降权、移出组织、禁用、退出租户、旧 session、旧 token、旧缓存。
14. 多入口差异：Web 页面、REST API、GraphQL、WebSocket、移动端接口、后台接口、worker、CLI、Webhook。
15. 旧版本接口：/v1、/legacy、/compat、/old、/admin-old、deprecated route。
16. fallback 路由：catch-all、通配符、动态路由、尾斜杠、大小写、URL 编码、重复斜杠、后缀格式、locale 前缀。
17. 框架默认行为：路由库、认证库、session 库、JWT 库、ORM、GraphQL、WebSocket、文件服务库的默认 allow、默认 trust header、默认 debug user、默认 mock auth。
18. 前后端不一致：前端隐藏按钮、隐藏菜单、隐藏参数、禁用按钮不等于后端安全；必须重放接口验证。

### 阶段 5：50 项非常规测试

从 `templates/output-template.md` 复制 UC-01 到 UC-50。每一项必须填：测试编号、测试入口、测试账号、测试资源、请求构造、预期结果、实际结果、证据文件、结论等级、修复建议。

不存在对应入口或技术栈时，实际结果写“未发现对应入口或技术栈”，结论等级写 blocked，证据文件指向暴露面矩阵或代码搜索记录。

### 阶段 6：证据分级

| 结论 | 使用条件 | 禁止情况 | 必须输出 |
|---|---|---|---|
| confirmed | 有真实动态请求、正反样本、异常成功结果、证据文件、可复现步骤 | 只有静态代码、只有 200、没有反向样本、没有证据 | findings.md 和回归测试 |
| candidate | 代码路径可疑但没有完整动态证据 | 不得写成 confirmed | 最小动态复现计划 |
| blocked | 环境、账号、依赖、启动失败、数据缺失无法验证 | 不得推测结论 | 阻塞原因、缺少什么、补齐方法 |
| false_positive | 动态验证证明没有问题 | 不得继续列为漏洞 | 排除依据和证据文件 |
| needs_review | 证据不完整或影响判断不稳定 | 不得强行定级 confirmed | 人工复核点和缺失证据 |

### 阶段 7：误报追责和漏测追责

对每个 confirmed 执行 25 项反查：

1. 是否真的启动了本地服务。
2. 是否真的创建或识别了不同角色账号。
3. 是否真的创建或识别了不同租户资源。
4. 是否真的用 user_a 请求了 user_b 的资源。
5. 是否真的用 tenant_a 请求了 tenant_b 的资源。
6. 是否真的用普通用户请求了管理员接口。
7. 是否真的有正向成功样本。
8. 是否真的有反向失败预期样本。
9. 是否真的出现了异常成功结果。
10. 是否记录了状态码、响应体、日志、数据库变化或测试输出。
11. 是否有 HAR、trace、截图、curl 或自动化测试。
12. 是否确认返回内容有敏感性或产生越权效果。
13. 是否排除“只是看到 200 就误判为越权”。
14. 是否排除“只是看到代码缺少 guard 就误判为 confirmed”。
15. 是否排除“把前端限制当成后端限制”。
16. 是否检查同资源的其他方法。
17. 是否检查批量接口。
18. 是否检查导出、下载、预览、附件。
19. 是否检查 GraphQL nested resolver。
20. 是否检查 WebSocket room / channel。
21. 是否检查异步任务和队列。
22. 是否检查旧版本接口和 legacy route。
23. 是否检查软删除、归档、草稿、审批状态。
24. 是否检查降权后旧 session。
25. 是否检查多租户缓存和导出文件缓存。

处理动作：

- 任一 confirmed 缺少动态证据：降级 candidate。
- 任一 candidate 缺复现计划：补 replay_plan。
- 任一 blocked 缺补齐方法：补 blocked.md。
- 任一 false_positive 缺排除依据：补 false_positives.md。
- 任一 confirmed 缺回归测试：补 evidence/tests/。

## 质量门禁

进入交付前必须逐项执行：

| 门禁编号 | 检查对象 | 通过标准 | 失败处理 |
|---|---|---|---|
| QG-00 | TXT 读取 | 已读取原始 TXT 或用户提供全文 | 未读取则停止，写“未验证，不得宣称已通过” |
| QG-01 | 授权范围 | 目标为本机、授权开源项目、本地服务或测试资源 | 动态请求全部 blocked |
| QG-02 | Skill 数量 | 保留 1 个主 Skill；若拆分必须证明输入输出完全不同 | 合并或删除多余 Skill |
| QG-03 | 命名 | 小写英文短横线，能对应“越权动态验证”主题，无 best/final/new/advanced/ultimate 等空泛词 | 重命名并更新引用 |
| QG-04 | 目录结构 | 仅保留 SKILL.md、README.md、templates、checklists、examples、tests | 删除空目录和无调用价值文件 |
| QG-05 | 原文/补强区分 | 映射表标明原文复刻或工程化补强 | 补映射，移除伪装为原文的新增项 |
| QG-06 | 项目画像 | 语言、框架、入口、启动、路由、权限模块有记录或 unknown | 补画像或写 unknown |
| QG-07 | 暴露面矩阵 | 16 个规定字段完整 | 补字段或 blocked |
| QG-08 | 动态环境 | 服务启动、数据库初始化、账号和资源准备有证据或 blocked | 补日志或 blocked |
| QG-09 | 正反对照 | 每个 confirmed 有正向和反向样本 | 降级 candidate |
| QG-10 | confirmed 证据 | 有异常成功结果、证据文件、可复现步骤 | 降级 candidate 或 needs_review |
| QG-11 | 误报追责 | 每个 confirmed 完成 25 项反查 | 未完成不得交付 |
| QG-12 | 50 项非常规测试 | UC-01 到 UC-50 均有结果或 blocked | 补齐结果 |
| QG-13 | 输出完整性 | 最终报告 13 部分齐全 | 补齐缺失部分 |
| QG-14 | 失败处理 | candidate、blocked、false_positive、needs_review 均按规则输出 | 重写结论区 |
| QG-15 | 空壳检测 | 不存在只有标题、没有字段、没有验收标准的文件 | 删除或重写 |

## 幻觉控制

1. 未读取 TXT，不得生成或审查 Skill。
2. 未读取某个 Skill 文件，不得宣称该文件通过。
3. 不确定字段写 unknown。
4. 未启动服务不得写“已动态验证”。
5. 未发起请求不得写 confirmed。
6. 没有正反对照不得写 confirmed。
7. 没有证据文件不得写 confirmed。
8. 代码缺少 guard 只能写 candidate，除非动态请求证明越权成功。
9. 前端隐藏按钮、隐藏菜单、禁用按钮不能作为后端安全证据。
10. 200 状态码不是越权证据；必须证明越界资源、敏感字段、状态变化或业务效果。
11. 自动化测试失败不能直接证明漏洞；必须排除环境、认证、数据和断言错误。
12. 工程化补强不得伪装为 TXT 原文。
13. 不生成针对公网或第三方目标的命令。

## 失败处理

| 场景 | 结论等级 | 必须记录 | 处理动作 |
|---|---|---|---|
| TXT 未读取 | blocked | 缺失 TXT 路径或全文 | 停止生成，输出“未验证” |
| 授权边界不明 | blocked | 缺失授权说明 | 只做静态画像，不做动态请求 |
| 项目不能启动 | blocked | 启动命令、错误日志、缺失依赖 | 写补齐命令或依赖清单 |
| 数据库不能初始化 | blocked | migration/seed 错误、连接配置 | 写测试数据库补齐方法 |
| 账号不能创建 | blocked | 账号类型、接口、字段、错误响应 | 写最小 fixture 方案 |
| 资源不能创建 | blocked | 资源类型、创建接口、失败原因 | 写 fixture 或手工创建步骤 |
| 只有静态可疑代码 | candidate | 代码文件、缺失校验点 | 写最小动态复现计划 |
| 动态请求成功但无敏感数据或越权效果 | needs_review | 状态码、响应字段、影响不确定点 | 写人工复核点 |
| 动态证明访问被拒绝 | false_positive | 请求、状态码、拒绝原因、证据 | 写排除依据 |
| confirmed 缺任一必要证据 | candidate | 缺失证据类型 | 降级并补 replay_plan |

## 输出格式

最终报告结构：

```text
# 1. 项目越权风险架构摘要
# 2. 越权暴露面矩阵
# 3. 多角色 / 多租户测试矩阵
# 4. 动态验证环境说明
# 5. 已确认高影响越权问题
# 6. 候选高风险线索
# 7. 已排除误报
# 8. 阻塞项和补齐办法
# 9. 小众 / 偏门路径专项结果
# 10. 依赖和框架默认行为风险
# 11. 修复建议
# 12. 回归测试清单
# 13. 下一轮深挖计划
```

confirmed findings 字段：

```text
漏洞标题：
类型：水平越权 / 垂直越权 / 多租户越权 / 文件越权 / GraphQL 越权 / WebSocket 越权 / 业务流越权
影响接口：
影响文件：
影响角色：
影响租户：
影响资源：
触发条件：
正向请求：
反向请求：
实际异常成功结果：
状态码：
响应关键字段：
数据库或日志证据：
HAR / trace / screenshot / curl / test output 路径：
可复现步骤：
最小修复建议：
修复后的回归测试：
严重性判断：
结论等级：confirmed
```

## 自检清单

- [ ] 已读取 TXT；未读取时已标“未验证，不得宣称已通过”。
- [ ] 目标范围是本机或授权项目。
- [ ] 未生成公网扫描或第三方攻击命令。
- [ ] 未使用真实用户数据。
- [ ] 未包含破坏性测试。
- [ ] 已读取项目结构，不是只看标题或 README。
- [ ] 已识别语言、框架、入口文件、启动命令或写 unknown/blocked。
- [ ] 已枚举 REST、GraphQL、WebSocket、文件、后台任务、前端 API client、旧接口或写未发现。
- [ ] 已识别用户、角色、权限、租户、组织、团队、资源归属字段或写 unknown。
- [ ] 已输出 16 字段越权暴露面矩阵。
- [ ] 已启动服务或写 blocked。
- [ ] 已创建或识别测试身份和测试资源或写 blocked。
- [ ] 每个 confirmed 有动态请求、正向样本、反向样本、异常成功结果、证据文件、复现步骤。
- [ ] 每个 candidate 有最小动态复现计划。
- [ ] 每个 blocked 有缺少什么和补齐方法。
- [ ] 每个 false_positive 有排除依据。
- [ ] 每个 needs_review 有人工复核点。
- [ ] 已完成 25 项 confirmed 追责。
- [ ] 已执行或 blocked 记录 UC-01 到 UC-50。
- [ ] 已生成回归测试清单。
- [ ] 已区分原文复刻和工程化补强。

## TXT 到 Skill 映射说明

| TXT 原文位置/标题 | Skill 文件 | 转化方式 | 原文复刻/工程化补强 | 备注 |
|---|---|---|---|---|
| 角色与工作范围 | SKILL.md 适用范围、不适用范围、阶段 0 | 转成授权边界与拒绝条件 | 原文复刻 | 不扩大到公网或第三方 |
| 禁止事项 1-9 | SKILL.md 不适用范围、幻觉控制、失败处理 | 转成 hard rules | 原文复刻 | 保留“无动态证据只能 candidate” |
| 目标漏洞类型列表 | SKILL.md 适用范围、原文复刻规则 | 转成验证对象清单 | 原文复刻 | 保留全部越权类型 |
| 第一阶段：项目暴露面建模 | SKILL.md 阶段 1、output-template.md | 转成画像步骤和 16 字段矩阵 | 原文复刻 | 字段不删减 |
| 第二阶段：动态验证环境准备 | SKILL.md 阶段 2、quality-gate.md | 转成启动、数据库、账号、资源准备流程 | 原文复刻 | 保留工具优先级 |
| 必需测试身份 | SKILL.md 原文复刻规则、output-template.md | 转成测试账号表 | 原文复刻 | 保留 10 类身份 |
| 必需测试资源 | SKILL.md 原文复刻规则、output-template.md | 转成测试资源表 | 原文复刻 | 保留 13 类资源 |
| 第三阶段：越权动态验证规则 | SKILL.md 阶段 3、examples | 转成正反样本流程 | 原文复刻 | 保留记录字段 |
| 第四阶段：重点深挖方向 | SKILL.md 阶段 4、quality-gate.md | 转成 18 类专项门禁 | 原文复刻 | 保留原顺序和对象 |
| 第五阶段：证据分级 | SKILL.md 阶段 6、失败处理 | 转成结论等级表 | 原文复刻 | confirmed 门槛严格保留 |
| 第六阶段：证据目录要求 | README.md、output-template.md | 转成 evidence/ 文件要求 | 原文复刻 | 不把可选索引伪装成原文 |
| 第七阶段：输出要求 | SKILL.md 输出要求、output-template.md | 转成 13 部分报告模板 | 原文复刻 | 标题保留 |
| 误报追责官 / 漏测追责官 | SKILL.md 阶段 7、final-review.md | 转成 25 项追责清单 | 原文复刻 | 失败即降级 |
| 50 项非常规测试方向 | output-template.md | 转成 UC-01 到 UC-50 表 | 原文复刻 | 每项 10 字段 |
| `AUTHZ-YYYYMMDD-NNN`、`evidence/_index.md` | SKILL.md 工程化补强规则 | 新增证据管理格式 | 工程化补强 | 不作为 confirmed 必要条件 |
| Skill 交付质量测试 | tests/skill-quality-tests.md | 新增检查 Skill 是否空壳、漏复刻、幻觉扩展 | 工程化补强 | 服务于验收 |
