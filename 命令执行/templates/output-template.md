# 命令执行风险动态验证报告模板

> 使用方式：复制本模板，逐项填写。没有证据的字段写“未验证+原因”或“不适用+原因”。不得编造命令输出、日志、截图、HAR、trace。

## 0. 报告元数据

| 字段 | 内容 |
|---|---|
| 项目路径 | `<project_root>` |
| 授权范围 | `<authorization_scope>` |
| 操作系统 | `<Windows/Linux/macOS>` |
| 测试环境启动方式 | `<commands or needs_environment>` |
| 测试数据库/测试目录 | `<path or description>` |
| marker 目录 | `<./security-lab/markers/>` |
| 证据目录 | `<./security-lab/evidence/>` |
| 可用角色 | `<roles>` |
| 可用租户 | `<tenants>` |
| 报告日期 | `<YYYY-MM-DD>` |

## 1. 边界确认

| 边界项 | 结论 | 证据/说明 |
|---|---|---|
| 仅当前本地授权项目 | `<yes/no>` | `<evidence>` |
| 仅测试环境/测试数据库/测试目录 | `<yes/no>` | `<evidence>` |
| 不访问公网敏感地址、内网敏感地址、云元数据地址 | `<yes/no>` | `<evidence>` |
| 不读取真实密钥、真实用户数据、真实配置秘密 | `<yes/no>` | `<evidence>` |
| 不执行破坏性动作和资源耗尽动作 | `<yes/no>` | `<evidence>` |
| 仅使用无害 marker | `<yes/no>` | `<marker design>` |

## 2. 项目理解结果

| 项目面 | 结果 | 证据位置 |
|---|---|---|
| 语言/框架 | `<value>` | `<file/path>` |
| 入口文件 | `<value>` | `<file/path>` |
| 启动方式 | `<value>` | `<file/path>` |
| 路由注册方式 | `<value>` | `<file/path>` |
| 认证方式 | `<value>` | `<file/path>` |
| 权限模型 | `<value>` | `<file/path>` |
| CLI | `<found/not found/not verified>` | `<file/path/reason>` |
| worker/queue/cron | `<found/not found/not verified>` | `<file/path/reason>` |
| webhook | `<found/not found/not verified>` | `<file/path/reason>` |
| 导入导出/文件处理链 | `<found/not found/not verified>` | `<file/path/reason>` |
| 插件/hook/extension | `<found/not found/not verified>` | `<file/path/reason>` |
| 第三方工具调用链 | `<found/not found/not verified>` | `<file/path/reason>` |

## 3. 命令执行暴露面总览

| 模块 | 入口 | source | sink | 权限 | 是否动态可达 | 风险等级 | 当前状态 |
|---|---|---|---|---|---|---|---|
| `<module>` | `<route/CLI/worker/webhook/import>` | `<source>` | `<sink>` | `<role/tenant>` | `<yes/no/unknown>` | `<critical/high/medium/low/info>` | `<confirmed/candidate/blocked/false_positive/needs_environment>` |

## 4. source 清单

| source 编号 | 类型 | 位置 | 权限/租户 | 说明 |
|---|---|---|---|---|
| `SRC-001` | `<HTTP/JSON/multipart/header/cookie/WebSocket/GraphQL/webhook/CLI/env/config/db/queue/template/file/archive/plugin/integration>` | `<path>` | `<role/tenant>` | `<description>` |

## 5. sink 清单

| sink 编号 | 类型 | 位置 | 调用方式 | 是否 shell 字符串 | 说明 |
|---|---|---|---|---|---|
| `SNK-001` | `<shell/subprocess/scheduler/script/file-converter/git/package-manager/db-client/wrapper/plugin/hook>` | `<path>` | `<api/tool>` | `<yes/no/unknown>` | `<description>` |

## 6. source → transform → sink 数据流图

| 数据流编号 | source | transform | sink | 安全机制 | 可达性 | 初始结论 |
|---|---|---|---|---|---|
| `DF-001` | `<SRC-001>` | `<normalization/validation/wrapper/queue/db>` | `<SNK-001>` | `<allowlist/escaping/arg-array/permission/fixed-cwd>` | `<reachable/blocked/unknown>` | `<candidate/blocked/needs_environment>` |

## 7. replay plan 清单

### 7.1 `<CMD-EXEC-YYYYMMDD-001>`

| 字段 | 内容 |
|---|---|
| 漏洞编号 | `<CMD-EXEC-YYYYMMDD-001>` |
| 入口点 | `<route/CLI/worker/webhook/file import/background job>` |
| 权限前提 | `<anonymous/user/admin/tenant user/local CLI user>` |
| 数据流 | `<source → transform → sink>` |
| 触发步骤 | `<local harmless replay steps>` |
| 无害 marker | `<unique marker string>` |
| marker 允许位置 | `<./security-lab/markers/...>` |
| 正向验证 | `<input, observation, proof of execution>` |
| 负向验证 | `<normal input / escaped input / low privilege / other tenant / fixed version>` |
| 证据 | `<request/response/log/stdout/stderr/exit-code/marker/call-stack/code>` |
| 初始结论等级 | `<candidate/needs_environment>` |

## 8. 已确认漏洞

> 只有“动态验证成功 + 至少两类交叉证据 + 负向验证 + source 到 sink 真实可达”的发现允许进入本节。

### 8.1 `<标题>`

| 字段 | 内容 |
|---|---|
| 漏洞编号 | `<CMD-EXEC-YYYYMMDD-001>` |
| 严重性 | `<critical/high/medium/low>` |
| 影响范围 | `<module/feature/tenant scope>` |
| 入口点 | `<entry>` |
| 受影响角色 | `<role>` |
| 受影响租户 | `<tenant/cross-tenant/no cross-tenant/not verified>` |
| source → sink 数据流 | `<source → transform → sink>` |
| 动态复现步骤 | `<local harmless replay steps>` |
| marker 证据 | `<marker file path/content or controlled stdout/stderr/exit code>` |
| 交叉证据 1 | `<evidence>` |
| 交叉证据 2 | `<evidence>` |
| 正向验证结果 | `<result>` |
| 负向验证结果 | `<result>` |
| 相关代码位置 | `<file:line>` |
| 依赖版本 | `<package/version if relevant>` |
| 环境信息 | `<OS/runtime>` |
| 根因 | `<specific root cause>` |
| 修复建议 | `<engineering fix>` |
| 修复后验证方法 | `<regression replay>` |
| 最终判决 | `confirmed` |

## 9. 候选漏洞

| 编号 | 为什么可疑 | 缺少什么动态证据 | 下一步最小验证 | 为什么不能升级为 confirmed |
|---|---|---|---|---|
| `<CMD-EXEC-...>` | `<static path/source-sink>` | `<missing env/log/marker/negative test>` | `<minimal local replay>` | `<reason>` |

## 10. 被阻断路径

| 编号 | 危险表象 | 阻断机制 | 验证样本 | 证据 | 结论 |
|---|---|---|---|---|---|
| `<CMD-EXEC-...>` | `<sink present>` | `<permission/allowlist/arg-array/fixed-cwd/schema>` | `<positive/negative sample>` | `<evidence>` | `blocked` |

## 11. false positive

| 编号 | 原误判原因 | 反证 | 结论 |
|---|---|---|---|
| `<CMD-EXEC-...>` | `<marker only echoed/logged/unreachable/demo code>` | `<why source does not reach sink>` | `false_positive` |

## 12. needs_environment

| 编号 | 缺失环境 | 影响 | 不能下结论的原因 | 后续最小补齐 |
|---|---|---|---|---|
| `<CMD-EXEC-...>` | `<worker/db/role/tenant/tool>` | `<dynamic validation unavailable>` | `<reason>` | `<setup>` |

## 13. 修复建议

| 问题类型 | 工程级修复 | 回归测试 |
|---|---|---|
| shell 字符串拼接 | 禁止 shell 字符串拼接，改用固定可执行文件路径和参数数组 | `<test>` |
| 参数注入 | 对 option、flag、子命令、路径、配置路径、插件路径、输出路径使用 allowlist | `<test>` |
| 文件处理链 | 文件名规范化、扩展名和 MIME 双校验、隔离工作目录、禁止用户控制输出路径 | `<test>` |
| worker 权限错位 | worker 最小权限运行，任务消息带租户上下文并在消费端校验 | `<test>` |
| 配置污染 | 禁止用户控制二进制路径、解释器路径、插件路径、临时目录、模板路径 | `<test>` |
| 导入导出/转换 | 租户隔离、固定工具参数、证据日志、回放测试 | `<test>` |

## 14. 第二轮反思

| 反思项 | 结论 | 证据/缺口 |
|---|---|---|
| 是否只盯着 HTTP，漏掉 CLI、worker、cron、webhook、import/export | `<checked/gap/not applicable>` | `<evidence>` |
| 是否只 grep 明显 API，漏掉 wrapper、adapter、helper、插件、事件监听器 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否漏掉数据库字段二次触发 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否漏掉文件名、压缩包条目名、metadata、content-type、输出路径 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否漏掉参数注入，只关注 shell 注入 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否漏掉多租户 worker 权限错位 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否误把普通回显当命令执行 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否有任何 confirmed 没有动态证据 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否对每个 confirmed 做了负向验证 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否有高危结论但没有最小复现 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否只测试 Linux，没考虑 Windows/macOS 参数解析差异 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否检查依赖工具本身的危险参数 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否检查隐藏参数、未文档化参数、后端接受但前端不暴露的参数 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否检查失败重试、异步补偿、日志处理、告警通知 | `<checked/gap/not applicable>` | `<evidence>` |
| 是否检查 admin-only 功能是否可被低权限用户间接触发 | `<checked/gap/not applicable>` | `<evidence>` |

## 15. 第三轮反常规补挖

| 反向路径 | 结果 | 新增发现编号 |
|---|---|---|
| 从所有外部工具调用反向找上游输入 | `<result>` | `<ids>` |
| 从所有用户可写数据库字段反向找后台消费点 | `<result>` | `<ids>` |
| 从所有文件落盘点反向找后续处理链 | `<result>` | `<ids>` |
| 从所有队列 topic/job name 反向找生产者 | `<result>` | `<ids>` |
| 从所有配置读取点反向找可写配置来源 | `<result>` | `<ids>` |
| 从所有插件/hook/extension 机制反向找用户可控入口 | `<result>` | `<ids>` |
| 从所有导入/恢复/迁移功能反向找命令链 | `<result>` | `<ids>` |
| 从所有 export/report/preview/render 功能反向找转换工具 | `<result>` | `<ids>` |
| 从所有 CI/build/test/devtool 调用反向找是否可由 Web 或项目配置触发 | `<result>` | `<ids>` |
| 从所有权限边界反向找低权限用户是否能污染高权限执行上下文 | `<result>` | `<ids>` |

## 16. confirmed 反向审判

| 编号 | 真实命令执行证据 | marker 来自真实子进程 | 至少两类交叉证据 | 已做负向验证 | 角色/租户影响已证明 | source 到 sink 可达 | 是否存在阻断机制 | 是否误判开发/demo/CVE | 最终判决 |
|---|---|---|---|---|---|---|---|---|---|
| `<CMD-EXEC-...>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<yes/no/not applicable>` | `<yes/no>` | `<yes/no>` | `<yes/no>` | `<confirmed/candidate/blocked/false_positive/needs_environment>` |

## 17. 未完成验证及原因

| 项目 | 原因 | 风险影响 | 后续最小动作 |
|---|---|---|---|
| `<item>` | `<reason>` | `<impact>` | `<action>` |

## 18. 最终结论

| 状态 | 数量 | 编号 |
|---|---:|---|
| confirmed | `<n>` | `<ids>` |
| candidate | `<n>` | `<ids>` |
| blocked | `<n>` | `<ids>` |
| false_positive | `<n>` | `<ids>` |
| needs_environment | `<n>` | `<ids>` |

```text
最终结论只写证据支持的内容。不得扩大影响范围。不得把未验证项写成已验证。
```
