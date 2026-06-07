# TXT 到 Skill 映射表

| TXT 原文位置/标题 | 原文关键内容 | 当前 Skill 位置 | 是否完整复刻 | 是否被改写失真 | 是否遗漏 | 修复动作 |
|---|---|---|---|---|---|---|
| 文件名：注入类提示词转skills.txt | 注入类、本地授权、动态验证 | `local-injection-verify/`、`SKILL.md` | 是 | 否 | 否 | 保留简洁英文短横线命名 |
| 角色设定 | 授权本地项目注入类缺陷动态验证负责人 | `SKILL.md` 适用范围、原文复刻规则 | 是 | 否 | 否 | 转为 Skill 触发语义 |
| 任务边界 | 不是泛泛扫描，不是只做静态审计；只允许本地授权测试；禁止破坏和越界；忽略 MITM | `SKILL.md` 不适用范围、质量门禁、失败处理 | 是 | 否 | 否 | 转为 hard rules |
| 核心目标 1-7 | 找候选、设计计划、无害 marker、状态分级、证据链、高危注入覆盖、无动态证据不得 confirmed | `SKILL.md` 输出要求、原文复刻规则、核心工作流 | 是 | 否 | 否 | 转为工作流和门禁 |
| 一、项目运行画像 | 识别语言、框架、入口、路由、数据库、ORM、模板、队列、任务、文件、GraphQL/WebSocket/RPC | `templates/output-template.md` 第 1 节；`SKILL.md` 阶段 1 | 是 | 否 | 否 | 转为画像表 |
| 外部输入来源 | HTTP、GraphQL、WebSocket、Webhook、文件、CLI、环境变量、后台任务、配置、模板、搜索、OAuth、第三方、二次读取字段 | `SKILL.md` 原文复刻规则；`quality-gate.md` | 是 | 否 | 否 | 转为覆盖门禁 |
| 解释器/危险 sink | SQL/NoSQL/ORM raw、命令、模板、表达式、XPath/LDAP/XML、regex、JSONPath、GraphQL、搜索 DSL、渲染器、反序列化、report/export、workflow/rule、cron、email | `SKILL.md` 原文复刻规则；`output-template.md` 第 12.6 节 | 是 | 否 | 否 | 转为边界枚举 |
| source-to-sink 数据流图 | source、参数、类型、路径、安全处理、最终解释器、角色、跨租户/跨角色/二阶 | `output-template.md` 第 2 节 | 是 | 否 | 否 | 转为矩阵字段 |
| 二、动态验证总规则 | 本地启动、测试库、测试账号/租户、唯一 marker、正向请求、负向对照、日志、HTTP、DB/文件对比、错误栈、复现步骤、安全限制 | `SKILL.md` 阶段 3/4；`output-template.md` 第 3/4 节 | 是 | 否 | 否 | 转为计划和结果模板 |
| 三、注入类型覆盖 | SQL、NoSQL、命令、模板/表达式、XPath/LDAP/XML、GraphQL、Header/CRLF、JSONPath/JMESPath/Regex/Search DSL、Import/Export、二阶 | `quality-gate.md`、`final-review.md`、`SKILL.md` 自检 | 是 | 否 | 否 | 转为勾选项 |
| 四、偏门与冷门路线 | 隐藏参数、非主流程、封装依赖、多解释器链、类型边界、权限组合 | `final-review.md`、`output-template.md` 第 6/7/12 节 | 是 | 否 | 否 | 转为专项反查 |
| 五、严重性判定 | high/critical confirmed 8 项证据；无动态验证只能 candidate | `SKILL.md` 质量门禁；`final-review.md` 严重性反查 | 是 | 否 | 否 | 转为降级门禁 |
| 六、输出格式 | 0-11 节报告格式 | `output-template.md` 第 0-11 节 | 是 | 否 | 否 | 转为模板 |
| 七、工作纪律 | 禁止编造、禁止静态当 confirmed、不可只查 SQL、不可忽略二阶/隐藏/任务/模板/搜索/角色、禁止破坏性步骤 | `quality-gate.md`、`SKILL.md` 幻觉控制 | 是 | 否 | 否 | 转为验收门禁 |
| 反向审判角色 | 拆穿、补全、降级证据不足结论 | `SKILL.md` 阶段 5；`final-review.md` | 是 | 否 | 否 | 转为最终审查流程 |
| confirmed 反查 10 项 | 启动、请求、正向、负向、marker、日志、DB/文件/任务、解释器处理、正常功能排除、回滚 | `final-review.md` confirmed 结论反查 | 是 | 否 | 否 | 转为 checklist |
| 24 类解释器 | SQL 到 logging/query system | `final-review.md`；`output-template.md` 第 12.6 节 | 是 | 否 | 否 | 转为反查表 |
| 二阶字段、隐藏参数、封装、角色/租户、非 HTTP、冷门检查点 | 各专项列表 | `final-review.md` | 是 | 否 | 否 | 转为可勾选清单 |
| 最终输出 13 项与最后问题 | 降级、新候选、漏项、最终清单、修复回归、仍可能漏掉什么 | `output-template.md` 第 12/13 节 | 是 | 否 | 否 | 转为报告章节 |
| ID、证据编号、脱敏、追溯目录、测试 | 为执行和验收新增 | `SKILL.md` 工程化补强；`tests/`；`source/`；`mappings/` | 是 | 否 | 否 | 标记为工程化补强 |
