# cmd-exec-risk-replay

## 适用范围

[原文复刻]
本 Skill 只用于当前本地授权开源项目的命令执行类风险动态验证。工作对象必须是本地项目中的真实代码、项目结构、依赖、语言特性、运行方式、路由、控制器、任务队列、CLI、插件机制、文件处理链、配置加载链、第三方工具调用链。

[工程化补强]
调用本 Skill 前，必须给出或由 Claude 从项目中确认：`project_root`、授权范围、测试环境、测试数据库或测试目录、marker 目录、证据目录、可用角色、可用租户、操作系统。缺少授权范围时停止；缺少测试环境时只允许静态候选记录，结论最高为 `needs_environment` 或 `candidate`。

## 不适用范围

[原文复刻]
不得用于未授权目标、生产数据、真实密钥、真实用户数据、真实配置秘密、公网敏感地址、内网敏感地址、云元数据地址。不得执行反弹 shell、下载执行、持久化、提权、横向移动、凭据读取、删库、删文件、业务破坏、DoS、DDoS、资源耗尽。忽略 MITM、网络劫持、证书绕过，本轮不把它们作为重点。

[工程化补强]
不得生成攻击投递包、规避检测步骤、持久化脚本、凭据读取流程、破坏性验证流程。所有动态验证必须限制在测试环境和 `./security-lab/` 这类项目内 sandbox 目录。

## 输入要求

[原文复刻]
必须先理解项目，再验证风险。输入材料至少包括项目代码、依赖声明、lockfile、配置、入口文件、启动方式、路由注册、认证方式、权限模型、worker/queue/cron、CLI、webhook、导入导出、文件处理链、插件/hook、第三方工具调用链。

[工程化补强]
推荐调用参数如下；用户未提供时，Claude 必须在报告中写明“从项目推断”或“未提供”。

```yaml
project_root: "<本地授权项目路径>"
authorization_scope: "<授权范围说明>"
runtime:
  os: "<Windows/Linux/macOS>"
  start_commands:
    - "<测试环境启动命令>"
  test_database: "<测试数据库或不适用>"
security_lab:
  marker_dir: "./security-lab/markers/"
  evidence_dir: "./security-lab/evidence/"
roles_and_tenants:
  roles: ["anonymous", "user", "admin"]
  tenants: ["tenant-a", "tenant-b"]
blocked_actions:
  network_sensitive_targets: true
  destructive_actions: true
  credential_access: true
  resource_exhaustion: true
```

缺少 `project_root`：不得开始。缺少 `authorization_scope`：不得验证。`marker_dir` 不可写：不得执行 marker 验证。环境无法启动：记录失败原因，结论不得超过 `needs_environment`。

## 输出要求

[原文复刻]
最终报告必须明确列出：`confirmed`、`candidate`、`blocked`、`false_positive`、`needs_environment`。每个 `confirmed` 必须有无害动态证据。不得编造命令输出、日志、截图、HAR、trace；未执行的验证不得写成已执行。

[工程化补强]
最终输出必须使用 `templates/output-template.md` 的结构，至少包含：边界记录、项目理解记录、暴露面总览、source 清单、sink 清单、source → transform → sink 数据流图、replay plan、动态验证记录、候选漏洞、确认漏洞、被阻断路径、误报、环境不足项、修复项、第二轮反思、第三轮补挖、confirmed 反向审判、最终结论。

## 原文复刻规则

[原文复刻]
执行顺序必须保持为：

1. 先锁定强制边界。
2. 再识别语言、框架、入口文件、启动方式、路由注册方式、认证方式、权限模型。
3. 再识别命令执行相关 sink：shell 命令执行 API、子进程 API、任务调度 API、脚本执行 API、模板渲染到命令链、文件转换工具调用、压缩/解压/图片/视频/PDF/Git/包管理器/构建工具/数据库客户端/系统工具包装器、自定义 wrapper/helper/adapter/service/plugin/hook。
4. 再识别 source：HTTP 参数、JSON body、multipart 文件名/字段名/content-type、header、cookie、WebSocket 消息、GraphQL 参数、webhook body、CLI 参数、环境变量、配置文件、数据库中可被用户写入的字段、队列消息、模板变量、文件路径、压缩包条目名、插件配置、第三方集成参数。
5. 再建立 source → transform → sink 数据流图，追踪 wrapper、别名、间接调用、异步队列、事件监听器、插件回调、任务 worker、ORM model hook、生命周期 hook。
6. 再按八类重点方向验证：直接命令拼接、参数注入、文件处理链触发、异步 worker 和后台任务、配置和环境变量间接污染、多角色多租户路径、依赖和框架特性、小众和偏门路径。
7. 每个候选点先生成 replay plan，再执行无害验证。
8. 每个 replay plan 必须包含漏洞编号、入口点、权限前提、数据流、触发步骤、无害 marker、正向验证、负向验证、证据、结论等级。
9. 验证严谨性必须覆盖：字符串回显不等于命令执行；日志出现 marker 不等于命令执行；参数进入函数不等于进入真实 sink；不可达代码不得标为漏洞；测试/demo/开发脚本不得直接标为生产可达；只有“可能存在风险”必须降级；参数数组仍要判断参数注入；存在 escaping、allowlist、schema validation、权限校验时必须用正负样本验证。
10. 输出报告必须包含暴露面总览、已确认漏洞、候选漏洞、被阻断路径、修复建议。
11. 第一轮后执行第二轮反思 15 项。
12. 第二轮后执行第三轮反常规补挖 10 项。
13. 最后反向审判每一个 `confirmed`，证据不足必须降级。

## 工程化补强规则

[工程化补强]
为避免摘要化和证据幻觉，增加以下规则：

1. 漏洞编号使用 `CMD-EXEC-YYYYMMDD-NNN`。
2. 每个发现必须绑定代码位置、配置位置或运行入口；缺失位置时不得标为 `confirmed`。
3. 每个 `confirmed` 至少需要两类交叉证据。可用证据包括：请求/响应、stdout、stderr、退出码、marker 文件、日志、调用栈、代码位置、依赖版本、环境信息、截图/trace、HAR 或等价请求记录、worker 日志。
4. 每个 `confirmed` 必须包含负向验证。缺少负向验证时降级为 `candidate`。
5. marker 只能写入 `marker_dir`，不能写入系统目录、用户目录、真实业务目录。
6. 动态验证不得联网访问敏感地址，不得读取真实密钥，不得破坏数据。
7. 使用参数数组、固定二进制路径、固定工作目录、allowlist、escaping、schema validation、权限校验时，必须记录它们是阻断点、弱化点还是仍可被参数注入影响。
8. 环境无法运行、角色缺失、租户缺失、worker 不可触发、依赖缺失时，记录到 `needs_environment`，不得补造证据。
9. 工程化补强只能作为执行约束，不得在报告中写成 TXT 原文要求。

## 核心工作流

### 阶段 0：边界锁定

输入：授权范围、项目路径、测试环境、marker 目录、证据目录。  
动作：确认只分析本地授权项目；确认只使用测试环境、测试数据库、测试目录；确认禁止目标和禁止动作；确认 marker 目录在项目内。  
输出：边界确认表。  
通过标准：授权范围、测试目录、禁止动作、marker 目录全部明确。  
失败处理：授权缺失则停止；marker 目录缺失则不执行动态验证。

### 阶段 1：项目初始化理解

输入：项目根目录。  
动作：识别语言、框架、入口文件、启动方式、路由、认证、权限模型、worker、CLI、webhook、导入导出、文件处理链、配置加载链、第三方工具调用链。  
输出：项目运行面清单。  
通过标准：Web、CLI、worker、webhook、导入导出、配置、依赖至少逐项标注“发现/未发现/未验证”。  
失败处理：无法读取项目则停止；无法启动则进入静态候选模式。

### 阶段 2：source 与 sink 枚举

输入：代码、配置、依赖、路由、worker、CLI。  
动作：按原文 source 与 sink 列表逐项枚举，记录代码位置、入口、权限、租户、可达性。  
输出：source 表、sink 表。  
通过标准：不能只搜索 API 名称，必须追踪 wrapper、别名、间接调用、异步链和 hook。  
失败处理：找不到 sink 时输出扫描范围和“未发现命令执行相关 sink”。

### 阶段 3：数据流图

输入：source 表、sink 表、调用链。  
动作：建立 source → transform → sink 路径，记录校验、转义、allowlist、参数数组、权限、租户、工作目录、二进制路径、配置路径、输出路径。  
输出：数据流图和候选优先级。  
通过标准：每条候选至少有 source、transform 或传递节点、sink、代码位置。  
失败处理：缺少动态入口则状态为 `candidate`；被安全机制阻断则状态为 `blocked`。

### 阶段 4：八类重点路径

输入：数据流图。  
动作：按原文顺序检查八类路径：直接命令拼接、参数注入、文件处理链、异步 worker、配置/环境污染、多角色多租户、依赖/框架特性、小众偏门路径。  
输出：候选发现表。  
通过标准：每类路径必须有“发现/未发现/未验证”结论。  
失败处理：未验证项进入 `needs_environment` 或 `candidate`，不得跳过。

### 阶段 5：replay plan

输入：候选发现表。  
动作：为每个候选写 replay plan，字段必须为漏洞编号、入口点、权限前提、数据流、触发步骤、无害 marker、正向验证、负向验证、证据、结论等级。  
输出：replay plan 清单。  
通过标准：没有 replay plan 的候选不得执行验证，也不得升级为 `confirmed`。  
失败处理：无法写出无害 replay 的候选保持 `candidate`。

### 阶段 6：无害动态验证

输入：replay plan、测试环境、marker 目录、证据目录。  
动作：执行正向验证和负向验证，只产生 marker 级证据。  
输出：动态验证记录。  
通过标准：`confirmed` 必须有执行证据、两类交叉证据、负向验证、可复现步骤。  
失败处理：只有字符串回显、只有日志、只有静态路径、环境不可用时不得 `confirmed`。

### 阶段 7：误报压降

输入：动态验证记录。  
动作：检查普通回显、日志误判、不可达代码、测试/demo/开发脚本、依赖 CVE 不可达、权限校验、allowlist、escaping、参数数组、固定工作目录。  
输出：降级表。  
通过标准：证据不足的发现必须降级。  
失败处理：结论和证据冲突时，以证据为准。

### 阶段 8：报告与修复项

输入：确认、候选、阻断、误报、环境不足记录。  
动作：按模板输出报告；修复项必须是工程级措施。  
输出：最终报告草案。  
通过标准：报告字段齐全，结论等级可追溯到证据。  
失败处理：缺字段时返回对应阶段补齐。

### 阶段 9：第二轮反思、第三轮补挖、confirmed 审判

输入：报告草案。  
动作：执行 `checklists/final-review.md`；逐个审判 `confirmed`。  
输出：修正后的最终报告。  
通过标准：每个 `confirmed` 均通过证据审判；不通过的立即降级。  
失败处理：不得保留证据不足的 `confirmed`。

## 分阶段执行步骤

1. 读取项目根目录和授权范围，建立边界确认表。
2. 创建或确认 `./security-lab/markers/` 与 `./security-lab/evidence/`；不可写时停止动态验证。
3. 读取 package manifest、lockfile、配置、入口、路由、CLI、worker、webhook、导入导出、文件处理链、插件和第三方工具调用。
4. 输出项目运行面清单，未发现的入口写“未发现”，未能验证的入口写“未验证+原因”。
5. 建立 source 表和 sink 表，记录代码位置。
6. 建立 source → transform → sink 数据流图，标注权限、租户、安全机制和可达性。
7. 按八类重点路径生成候选发现。
8. 为每个候选生成 replay plan。
9. 对允许验证的候选执行 marker 级正向验证。
10. 对同一候选执行负向验证：正常输入、转义输入、权限不足角色、其他租户、修复后样本；项目不支持的项写“不适用+原因”。
11. 汇总证据并判定状态。
12. 对证据不足的项降级。
13. 生成报告。
14. 执行第二轮反思。
15. 执行第三轮反常规补挖。
16. 逐个审判 `confirmed`。
17. 输出修正后的最终报告。

## 质量门禁

- [ ] 已确认目标为当前本地授权项目。
- [ ] 已确认验证只发生在测试环境、测试数据库、测试目录。
- [ ] 已确认不访问公网敏感地址、内网敏感地址、云元数据地址。
- [ ] 已确认不读取真实密钥、真实用户数据、真实配置秘密。
- [ ] 已确认不执行反弹 shell、下载执行、持久化、提权、横向移动、凭据读取、删库、删文件、业务破坏、DoS、DDoS、资源耗尽。
- [ ] 已确认 marker 目录在项目测试目录内且可写。
- [ ] 已识别语言、框架、入口、启动方式、路由、认证、权限模型。
- [ ] 已识别 source、sink，并建立 source → transform → sink 数据流图。
- [ ] 已覆盖八类重点路径，未发现或未验证均有记录。
- [ ] 每个候选点都有 replay plan。
- [ ] 每个 `confirmed` 有至少两类交叉证据。
- [ ] 每个 `confirmed` 有负向验证。
- [ ] 每个 `confirmed` 已通过最终反向审判。
- [ ] 证据不足的项已降级。
- [ ] 报告明确列出 `confirmed`、`candidate`、`blocked`、`false_positive`、`needs_environment`。

## 幻觉控制

- 没有读取项目文件时，不得描述项目结构。
- 没有运行验证时，不得写“已复现”。
- 没有 marker、stdout/stderr、退出码、调用栈、请求响应、worker 日志等证据时，不得写 `confirmed`。
- marker 只出现在日志或响应回显中，不得写 `confirmed`。
- 只有依赖 CVE，不得写当前项目可利用。
- 只有测试/demo/开发脚本，不得写生产可达。
- 只有 shell API 名称，不得写 source 到 sink 可达。
- 无法启动环境、无法登录、无法触发 worker、无法构造角色/租户样本时，写 `needs_environment`。
- 报告中的每个结论必须引用证据字段或失败原因。

## 失败处理

| 失败场景 | 处理 |
|---|---|
| 未提供项目路径 | 停止；要求项目路径 |
| 未提供授权范围 | 停止；不得验证 |
| 测试环境无法启动 | 记录启动命令、错误、缺失依赖；状态为 `needs_environment` |
| marker 目录不可写 | 不执行动态验证；候选最高为 `candidate` |
| 只能找到静态路径 | 状态为 `candidate` |
| source 无法到达 sink | 状态为 `false_positive` |
| 被权限、allowlist、schema validation、参数数组、固定工作目录阻断 | 状态为 `blocked`，记录阻断点 |
| 仅字符串回显或日志出现 marker | 状态为 `false_positive` 或 `candidate`，不得 `confirmed` |
| 缺少负向验证 | 降级为 `candidate` |
| 缺少第二类证据 | 降级为 `candidate` |
| 缺少角色/租户样本 | 对角色/租户影响写“未验证”，不得扩大影响范围 |

## 输出格式

必须使用 `templates/output-template.md`。关键章节如下：

1. 边界确认。
2. 项目理解结果。
3. 暴露面总览。
4. source 清单。
5. sink 清单。
6. source → transform → sink 数据流图。
7. replay plan 清单。
8. 已确认漏洞。
9. 候选漏洞。
10. 被阻断路径。
11. false positive。
12. needs_environment。
13. 修复建议。
14. 第二轮反思。
15. 第三轮反常规补挖。
16. confirmed 反向审判。
17. 未完成验证及原因。
18. 最终结论。

## 自检清单

- [ ] 我是否只验证当前本地授权项目。
- [ ] 我是否只在测试环境、测试数据库、测试目录中验证。
- [ ] 我是否避免了所有禁止动作和禁止目标。
- [ ] 我是否识别了 Web、CLI、worker、webhook、导入导出、配置、依赖。
- [ ] 我是否列出 source 和 sink。
- [ ] 我是否建立 source → transform → sink 数据流图。
- [ ] 我是否为每个候选写 replay plan。
- [ ] 我是否使用唯一无害 marker。
- [ ] 我是否做了正向验证和负向验证。
- [ ] 我是否把只有静态路径的项保留为 `candidate`。
- [ ] 我是否把阻断路径标为 `blocked`。
- [ ] 我是否把普通回显、不可达路径、demo/开发脚本误判降级。
- [ ] 我是否执行第二轮反思。
- [ ] 我是否执行第三轮反常规补挖。
- [ ] 我是否审判并降级证据不足的 `confirmed`。

## TXT 到 Skill 映射说明

| TXT 原文位置/标题 | Skill 文件 | 转化方式 | 原文复刻/工程化补强 | 备注 |
|---|---|---|---|---|
| 角色设定与总任务 | `SKILL.md` 适用范围、核心工作流 | 转为适用范围和执行目标 | 原文复刻 | 保留“不是泛泛静态审计，而是动态验证” |
| 一、强制边界 | `SKILL.md` 不适用范围、质量门禁、失败处理；`checklists/quality-gate.md` | 转为 hard rules 和 gate | 原文复刻 | 禁止动作未弱化 |
| 二、初始化工作 | `SKILL.md` 输入要求、阶段 1、阶段 2 | 转为项目理解、source/sink 枚举 | 原文复刻 | 保留 wrapper、hook、异步链要求 |
| 三、重点挖掘方向 | `SKILL.md` 阶段 4；`checklists/quality-gate.md` | 转为八类固定检查路径 | 原文复刻 | 按原顺序执行 |
| 四、动态验证要求 | `SKILL.md` 阶段 5/6；`templates/output-template.md` replay plan | 转为 replay plan 模板和验证字段 | 原文复刻 | 保留十项 replay 字段 |
| 五、验证严谨性 | `SKILL.md` 幻觉控制、失败处理；`checklists/final-review.md` | 转为误报压降规则 | 原文复刻 | 明确降级条件 |
| 六、输出格式 | `templates/output-template.md` | 转为可填写报告模板 | 原文复刻 | 保留暴露面、confirmed、candidate、blocked、修复建议 |
| 七、自我反思和反查 | `checklists/final-review.md` | 转为第二轮反思 checklist | 原文复刻 | 保留 15 项 |
| 八、第三轮偏门补充 | `checklists/final-review.md` | 转为第三轮补挖 checklist | 原文复刻 | 保留 10 项 |
| 九、最终硬性要求 | `SKILL.md` 输出要求、幻觉控制；`templates/output-template.md` 最终结论 | 转为最终判定和禁止编造规则 | 原文复刻 | 保留五类结论 |
| 末尾 confirmed 复核 | `checklists/final-review.md` confirmed 反向审判；`templates/output-template.md` confirmed 审判表 | 转为逐漏洞审判表 | 原文复刻 | 证据不足必须降级 |
| 文件结构、编号、测试 | `README.md`、`tests/skill-quality-tests.md` | 转为交付和验收辅助 | 工程化补强 | 未伪装成原文 |
