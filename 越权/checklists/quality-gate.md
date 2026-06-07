# 质量门禁清单

## A. TXT 与交付源文件门禁

- [ ] 已重新读取原始 TXT；未读取时写“未验证，不得宣称已通过”。
- [ ] 已重新读取 SKILL.md；未读取时写“未验证，不得宣称已通过”。
- [ ] 已重新读取 README.md；未读取时写“未验证，不得宣称已通过”。
- [ ] 已重新读取 templates/output-template.md；未读取时写“未验证，不得宣称已通过”。
- [ ] 已重新读取 checklists/quality-gate.md；未读取时写“未验证，不得宣称已通过”。
- [ ] 已重新读取 checklists/final-review.md；未读取时写“未验证，不得宣称已通过”。
- [ ] 已重新读取 examples/basic-example.md；未读取时写“未验证，不得宣称已通过”。
- [ ] 已重新读取 examples/full-example.md；未读取时写“未验证，不得宣称已通过”。
- [ ] 已重新读取 tests/skill-quality-tests.md；未读取时写“未验证，不得宣称已通过”。
- [ ] 已建立 TXT 到 Skill 映射表。
- [ ] 已区分原文复刻和工程化补强。

## B. Skill 数量与命名门禁

- [ ] 只保留 1 个主 Skill。
- [ ] 未拆出重复 Skill。
- [ ] 未拆出不能独立运行的 Skill。
- [ ] 未使用 best、final、new、advanced、ultimate、skill-only 等空泛词。
- [ ] 文件夹名使用小写英文和短横线。
- [ ] 文件夹名能看出“越权动态验证”主题。
- [ ] 不存在 README-final.md、new-template.md、copy.md 等低质量命名。

## C. 目录和文件门禁

- [ ] 最终目录只包含 SKILL.md、README.md、templates、checklists、examples、tests。
- [ ] 不存在空目录。
- [ ] 不存在只有标题没有字段的模板。
- [ ] 不存在只有口号没有验收标准的 checklist。
- [ ] 不存在无法发现问题的 tests。
- [ ] 每个文件都有明确作用。
- [ ] 每个文件能追溯到 TXT 原文或工程化补强理由。

## D. SKILL.md 必备章节门禁

- [ ] 适用范围。
- [ ] 不适用范围。
- [ ] 输入要求。
- [ ] 输出要求。
- [ ] 原文复刻规则。
- [ ] 工程化补强规则。
- [ ] 核心工作流。
- [ ] 分阶段执行步骤。
- [ ] 质量门禁。
- [ ] 幻觉控制。
- [ ] 失败处理。
- [ ] 输出格式。
- [ ] 自检清单。
- [ ] TXT 到 Skill 映射说明。

## E. 授权和安全边界门禁

- [ ] 目标是本机项目、授权开源项目或本地测试服务。
- [ ] 未生成公网扫描命令。
- [ ] 未生成第三方真实系统攻击命令。
- [ ] 未使用真实用户数据。
- [ ] 未包含中间人、流量劫持、证书劫持、钓鱼、社工。
- [ ] 未包含 DoS、DDoS、压力破坏、批量爆破。
- [ ] 未包含删除数据库或破坏业务数据。
- [ ] 未通过修改生产逻辑制造漏洞。

## F. 项目画像门禁

- [ ] 已识别或 blocked 记录编程语言。
- [ ] 已识别或 blocked 记录框架。
- [ ] 已识别或 blocked 记录入口文件。
- [ ] 已识别或 blocked 记录启动命令。
- [ ] 已识别路由注册方式。
- [ ] 已检查 controller、handler、resolver、service。
- [ ] 已检查 middleware、guard、policy、decorator、interceptor。
- [ ] 已识别用户、角色、权限、租户、组织、团队、资源归属模型。
- [ ] 已识别权限判断函数、租户过滤函数、owner 校验函数。
- [ ] 已枚举 REST API。
- [ ] 已枚举 GraphQL schema、query、mutation、resolver；不存在时已说明。
- [ ] 已枚举 WebSocket event、room、channel、subscription；不存在时已说明。
- [ ] 已枚举文件上传、下载、预览、导出、导入接口。
- [ ] 已枚举后台任务、队列、定时任务、Webhook、OAuth 回调、邀请、重置密码、邮箱绑定流程。
- [ ] 已检查前端路由、懒加载 JS、API client、权限按钮、隐藏菜单、隐藏参数。
- [ ] 已检查路由、鉴权、会话、ORM、GraphQL、WebSocket、文件处理相关依赖。

## G. 暴露面矩阵门禁

- [ ] `evidence/authz_surface_matrix.md` 已创建或 blocked。
- [ ] 每个入口都有入口名称。
- [ ] 每个入口都有请求方法或事件名。
- [ ] 每个入口都有路径 / resolver / handler。
- [ ] 每个入口都有代码文件或 unknown。
- [ ] 每个入口都有资源类型。
- [ ] 每个入口都有资源归属字段或 unknown。
- [ ] 每个入口都有预期访问角色。
- [ ] 每个入口都有预期禁止角色。
- [ ] 每个入口都有预期租户边界。
- [ ] 每个入口都有权限校验位置或 unknown。
- [ ] 每个入口都有可能缺失的校验点。
- [ ] 每个入口都有动态验证方法。
- [ ] 每个入口都有正向样本。
- [ ] 每个入口都有反向样本。
- [ ] 每个入口都有证据需求。
- [ ] 当前状态只使用 untested、candidate、confirmed、false_positive、blocked、needs_review。

## H. 动态环境门禁

- [ ] 服务真实启动，启动日志已保存；否则 blocked。
- [ ] 本地 base URL 可访问；否则 blocked。
- [ ] 数据库初始化方式已执行或 blocked。
- [ ] seed / fixture 已执行或 blocked。
- [ ] 登录或鉴权流程已执行或 blocked。
- [ ] 必需测试身份已创建/识别或 blocked。
- [ ] 必需测试资源已创建/识别或 blocked。
- [ ] 未修改业务安全逻辑。

## I. confirmed 结论门禁

- [ ] confirmed 有真实动态请求。
- [ ] confirmed 有正向成功样本。
- [ ] confirmed 有反向失败预期样本。
- [ ] confirmed 有异常成功结果。
- [ ] confirmed 不是只基于 200 状态码。
- [ ] confirmed 不是只基于静态代码缺 guard。
- [ ] confirmed 有响应关键字段、越界资源、状态变化或业务效果证据。
- [ ] confirmed 有数据库变化、服务端日志、HAR、trace、截图、curl 或自动化测试输出之一。
- [ ] confirmed 有可复现步骤。
- [ ] confirmed 有最小修复建议。
- [ ] confirmed 有修复后的回归测试。
- [ ] confirmed 已通过 25 项误报追责检查。

## J. candidate / blocked / false_positive / needs_review 门禁

- [ ] candidate 写明可疑代码文件。
- [ ] candidate 写明缺失的动态证据。
- [ ] candidate 写明最小动态复现计划。
- [ ] blocked 写明阻塞原因。
- [ ] blocked 写明缺少什么。
- [ ] blocked 写明本地补齐方法。
- [ ] false_positive 写明动态请求。
- [ ] false_positive 写明拒绝结果。
- [ ] false_positive 写明排除依据。
- [ ] needs_review 写明证据不稳定点和人工复核点。

## K. 非常规测试门禁

- [ ] UC-01 到 UC-50 均有结果行。
- [ ] 不存在对应入口或技术栈时，相关测试写 blocked，不删除测试项。
- [ ] 每项包含测试编号、测试入口、测试账号、测试资源、请求构造、预期结果、实际结果、证据文件、结论等级、修复建议。
- [ ] GraphQL 项不存在时，说明 schema/resolver 未发现。
- [ ] WebSocket 项不存在时，说明 event/room/channel 未发现。
- [ ] 文件项不存在时，说明上传/下载/预览/导出入口未发现。

## L. 交付门禁

- [ ] `evidence/authz_surface_matrix.md` 存在且字段完整，或 blocked 说明完整。
- [ ] `evidence/test_accounts.json` 存在或 blocked 说明完整。
- [ ] `evidence/test_resources.json` 存在或 blocked 说明完整。
- [ ] `evidence/replay_plan.md` 包含所有 candidate 最小复现计划。
- [ ] `evidence/replay_results.json` 包含动态请求结果或 blocked。
- [ ] `evidence/findings.md` 只包含 confirmed。
- [ ] `evidence/false_positives.md` 包含排除依据。
- [ ] `evidence/blocked.md` 包含补齐办法。
- [ ] 最终报告包含 13 个规定部分。
- [ ] 原文复刻与工程化补强已区分。
