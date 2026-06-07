# 质量门禁清单

## 1. Skill 交付门禁

用于审查或再次生成本 Skill。缺一项不得宣称通过。

- [ ] 已重新读取原始 TXT。
- [ ] 已重新读取 Skills 目录结构。
- [ ] 已重新读取 `SKILL.md`。
- [ ] 已重新读取 `README.md`。
- [ ] 已重新读取 `templates/output-template.md`。
- [ ] 已重新读取 `checklists/quality-gate.md`。
- [ ] 已重新读取 `checklists/final-review.md`。
- [ ] 已重新读取 `examples/basic-example.md`。
- [ ] 已重新读取 `examples/full-example.md`。
- [ ] 已重新读取 `tests/skill-quality-tests.md`。
- [ ] 无法读取的文件已标记为“未验证，不得宣称已通过”。
- [ ] 已建立 TXT 到 Skill 映射表。
- [ ] 已区分原文复刻和工程化补强。
- [ ] 未把工程化补强伪装成 TXT 原文。
- [ ] 未读取 TXT 时不得生成或修改 Skill。
- [ ] 未覆盖 TXT 关键章节时不得通过。
- [ ] 未提供模板时不得通过。
- [ ] 未提供 checklist 时不得通过。
- [ ] 未提供 examples 时不得通过。
- [ ] 未提供 tests 时不得通过。
- [ ] 未定义失败处理时不得通过。
- [ ] 文件命名无法对应 TXT 核心主题时不得通过。
- [ ] Skill 数量无理由超过 1 个时不得通过。
- [ ] 存在空壳目录或空壳文件时不得通过。
- [ ] 输出不可追溯 TXT 时不得通过。

## 2. Skill 数量和命名门禁

- [ ] 只保留 1 个主 Skill。
- [ ] 不存在多个 Skills 做同一件事。
- [ ] 不存在只改名字但内容重复的 Skills。
- [ ] 不存在不能独立运行的 Skills。
- [ ] 不存在只包含概念说明的 Skills。
- [ ] 目录结构没有增加 Claude 调用成本。
- [ ] 目录名使用小写英文和短横线。
- [ ] 目录名不含 best、final、new、advanced、ultimate、skill-only。
- [ ] 目录名能对应 TXT 核心主题：本地授权认证门禁动态验证。
- [ ] 文件名简洁且能区分用途。
- [ ] 不存在 `README-final.md`、`new-template.md`、`copy.md` 等低质量命名。

## 3. 范围门禁

- [ ] 目标是当前本地项目、当前仓库、当前本地运行环境。
- [ ] 未访问公网目标或第三方真实系统。
- [ ] 未使用真实用户数据。
- [ ] 未使用中间人、嗅探、证书劫持、流量劫持、钓鱼、社工路线。
- [ ] 未执行 DoS、压力测试、不可回滚删除或生产数据修改。
- [ ] 所有写操作使用测试数据库、事务、fixture、seed 数据或可回滚测试资源。
- [ ] 所有凭据、token、secret 已脱敏或仅写本地引用路径。

## 4. 暴露面矩阵门禁

- [ ] 已识别项目语言、框架、入口文件、启动方式。
- [ ] 已识别路由注册位置、middleware 链、认证模块、权限模块、session/token 模块。
- [ ] 已检查 User、Role、Permission、Tenant、Org、Team、Session、Token、APIKey、Invite、ResetPassword、EmailBinding、OAuthAccount 等实体。
- [ ] 已记录 HTTP 路由、GraphQL schema、WebSocket event、RPC handler、后台任务入口、文件上传下载入口、导入导出入口。
- [ ] 已记录认证装饰器、中间件、guard、policy、interceptor、filter、resolver、hook。
- [ ] 已检查前端路由、前端权限判断、隐藏菜单、隐藏按钮、隐藏接口、懒加载 JS、sourcemap、环境配置、API client 封装。
- [ ] 已检查认证、会话、权限、路由、序列化、模板、文件、GraphQL、WebSocket 相关依赖。
- [ ] `evidence/auth_surface_matrix.md` 已包含全部必填列。
- [ ] 静态风险只写为 `candidate`、`needs_review` 或 `blocked`。

## 5. 动态环境门禁

- [ ] 已找到或记录缺失的启动命令。
- [ ] 已找到或记录缺失的测试数据库初始化方式。
- [ ] 已找到或记录缺失的 seed、fixture、测试账号创建方式。
- [ ] 已创建或识别 anonymous、user_a、user_b、manager_a、admin、disabled_user、unverified_user、expired_session_user。
- [ ] 服务启动结果已记录为 true/false。
- [ ] 服务启动失败时，错误日志和本地补齐方式已写入 blocked。
- [ ] base_url 限定为 localhost、127.0.0.1、本机容器地址或用户明确授权的本地服务。
- [ ] `evidence/test_accounts.json` 已生成，或 blocked 原因已记录。

## 6. 正反验证门禁

- [ ] 每个入口都有合法账号访问合法资源的正向样本，或有 blocked 原因。
- [ ] 每个受保护入口都有 anonymous 反向样本，或有 blocked 原因。
- [ ] 用户私有资源已测试 user_a 访问 user_b 资源。
- [ ] 多租户资源已测试 tenant_a 访问 tenant_b 资源。
- [ ] 管理接口已测试普通用户访问。
- [ ] 账号状态已测试 disabled_user 和 unverified_user。
- [ ] 会话状态已测试 logout 后旧凭据和过期 token。
- [ ] 身份字段已测试 path/query/body/header/cookie/session 来源差异。
- [ ] 批量参数、嵌套 JSON、GraphQL variables、WebSocket payload 中的身份字段已测试，或记录项目不存在。
- [ ] 每个失败预期都记录状态码、响应字段、日志/DB/测试输出或替代证据。

## 7. 小众路径门禁

- [ ] 路由顺序：已测 fallback、catch-all、动态路由优先级，或记录项目不存在。
- [ ] 中间件遗漏：已测 list/detail/update/delete/export/import 一致性，或记录项目不存在。
- [ ] 方法差异：已测 GET/POST/PUT/PATCH/DELETE/OPTIONS/HEAD 中项目支持的方法。
- [ ] 内容类型差异：已测 JSON、form-data、x-www-form-urlencoded、text/plain、GraphQL variables 中项目支持的解析路径。
- [ ] 参数来源差异：已测 path/query/body/header/cookie/session 中身份字段优先级。
- [ ] 批量接口：已测 ids/items/filters/where/include/expand/fields/sort/ownerId/tenantId。
- [ ] 状态机：已测 deleted/disabled/pending/draft/archived/approved/rejected/cancelled/expired。
- [ ] 邀请与重置：已测 invite/reset/email bind/OAuth bind token。
- [ ] 多租户隔离：已测 tenant_id 是否来自客户端或可覆盖。
- [ ] 本地缓存：已测用户 A 结果是否可能返回给用户 B。
- [ ] 异步任务：已测提交时与执行时校验一致性。
- [ ] 文件资源：已测上传、下载、预览、导出、头像、附件、临时文件、私有文件 URL。
- [ ] GraphQL：已测 resolver、nested resolver、fragment、alias、batch query、introspection。
- [ ] WebSocket：已测连接校验与消息处理校验一致性。
- [ ] 依赖默认行为：已测默认 allow、trust header、跳过校验配置。
- [ ] 30 类非常规认证门禁测试计划均已填写结果或 blocked/not_applicable 原因。

## 8. confirmed 门禁

只有全部勾选，才能写 `confirmed`：

- [ ] 动态请求已经执行。
- [ ] 有正向成功样本。
- [ ] 有反向失败预期样本。
- [ ] 有异常成功结果或明确越权效果。
- [ ] 有测试账号、测试资源、测试租户。
- [ ] 有 HTTP 状态码。
- [ ] 有响应关键字段。
- [ ] 有数据库变化、日志证据、测试输出、HAR、trace、截图、curl 或测试用例之一。
- [ ] 能说明为什么不是测试误差。
- [ ] 有最小修复建议。
- [ ] 有修复后的 negative test。
- [ ] 有严重性判断依据。
- [ ] 标明跨用户、跨角色、跨租户、跨状态、跨认证方式影响。
- [ ] evidence/ 中的材料足以让另一名审计人员复现。

## 9. candidate 门禁

- [ ] 有明确风险假设。
- [ ] 有受影响入口、文件或函数。
- [ ] 有静态依据或未完成动态证据。
- [ ] 有最小动态复现实验。
- [ ] 写明还缺什么证据。
- [ ] 写明为什么不能确认为 confirmed。

## 10. blocked 门禁

- [ ] 写明阻塞原因。
- [ ] 写明已查找的位置。
- [ ] 写明缺失输入或环境。
- [ ] 写明本地补齐方式。
- [ ] 写明补齐后第一条验证命令。
- [ ] 未把 blocked 项写成 confirmed。

## 11. false positive 门禁

- [ ] 写明原风险假设。
- [ ] 有正向测试结果。
- [ ] 有反向测试结果。
- [ ] 有排除依据。
- [ ] 有证据文件。
- [ ] 未因单个 403 停止同资源其他路径测试。

## 12. 报告门禁

- [ ] findings.md 包含 confirmed、candidate、false_positive、blocked、needs_review 分区。
- [ ] 每个 confirmed 均有修复建议和回归测试。
- [ ] 每个 candidate 均有复现实验。
- [ ] 每个 blocked 均有补齐方式。
- [ ] 报告中没有未标证据的断言。
- [ ] 报告中没有把工程化补强伪装成原文能力。
