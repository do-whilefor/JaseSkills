# full-example

> 本示例只展示报告结构和证据写法，不提供破坏性 payload。示例中的项目、文件和 marker 均为占位内容。

## 0. 报告元数据

| 字段 | 内容 |
|---|---|
| 项目路径 | `C:\work\demo-app` |
| 授权范围 | 仅本地测试环境 |
| 操作系统 | Windows |
| marker 目录 | `./security-lab/markers/` |
| 证据目录 | `./security-lab/evidence/` |
| 可用角色 | user, admin |
| 可用租户 | tenant-a, tenant-b |

## 1. 项目理解结果

| 项目面 | 结果 | 证据位置 |
|---|---|---|
| 语言/框架 | Node.js + Express | `package.json`, `src/app.js` |
| 路由注册方式 | Express router | `src/routes/import.js` |
| worker | 发现 | `src/workers/report-worker.js` |
| CLI | 未发现 | 未发现 `bin` 或 CLI 入口 |
| 文件处理链 | 发现 | `src/services/converter.js` |

## 2. 暴露面总览

| 模块 | 入口 | source | sink | 权限 | 是否动态可达 | 风险等级 | 当前状态 |
|---|---|---|---|---|---|---|---|
| import | `/import` | multipart filename | converter wrapper | user/tenant-a | yes | high | candidate |
| report | queue worker | db report title | PDF converter | worker/admin context | unknown | medium | needs_environment |
| admin tools | admin route | JSON body | fixed arg array | admin | no | info | blocked |

## 3. source → transform → sink 数据流图

| 数据流编号 | source | transform | sink | 安全机制 | 可达性 | 初始结论 |
|---|---|---|---|---|---|
| DF-001 | multipart filename | normalizeUploadName → converter args | converter wrapper | extension allowlist 未覆盖 option | reachable | candidate |
| DF-002 | db report title | queue payload → report-worker | PDF converter | worker 未启动 | unknown | needs_environment |
| DF-003 | JSON body | schema validation | fixed arg array | allowlist + fixed cwd | blocked | blocked |

## 4. replay plan

### CMD-EXEC-20260607-001

| 字段 | 内容 |
|---|---|
| 入口点 | `/import` |
| 权限前提 | user，tenant-a |
| 数据流 | multipart filename → normalizeUploadName → converter wrapper |
| 触发步骤 | 启动测试环境；使用测试账号登录；上传测试文件；触发转换；收集响应、日志、marker 目录 |
| 无害 marker | `MARKER-CMD-EXEC-20260607-001` |
| marker 允许位置 | `./security-lab/markers/CMD-EXEC-20260607-001.txt` |
| 正向验证 | 只观察受控 stdout/stderr、退出码、marker 文件或 worker 日志 |
| 负向验证 | 正常文件名、转义文件名、低权限角色、tenant-b |
| 证据 | 请求响应、converter 日志、marker 文件、代码位置 |
| 初始结论等级 | candidate |

## 5. 候选漏洞

| 编号 | 为什么可疑 | 缺少什么动态证据 | 下一步最小验证 | 为什么不能升级为 confirmed |
|---|---|---|---|---|
| CMD-EXEC-20260607-001 | 用户文件名进入 converter wrapper 参数 | 尚未取得两类交叉证据和负向验证 | 在测试环境执行 marker 级 replay | 当前只有静态路径 |

## 6. 被阻断路径

| 编号 | 危险表象 | 阻断机制 | 验证样本 | 证据 | 结论 |
|---|---|---|---|---|---|
| CMD-EXEC-20260607-003 | admin route 调用外部工具 | schema validation + 参数 allowlist + fixed cwd | 正常样本和越界样本 | schema 拒绝越界参数，日志无 sink 调用 | blocked |

## 7. needs_environment

| 编号 | 缺失环境 | 影响 | 不能下结论的原因 | 后续最小补齐 |
|---|---|---|---|---|
| CMD-EXEC-20260607-002 | report worker 未能启动 | 无法验证 db 字段二次触发 | 没有 worker 日志和 marker 证据 | 补齐队列服务后重放 report job |

## 8. 第二轮反思摘要

| 反思项 | 结论 | 证据/缺口 |
|---|---|---|
| 是否只盯着 HTTP，漏掉 CLI、worker、cron、webhook、import/export | 已检查 | worker 进入 needs_environment，CLI 未发现 |
| 是否漏掉参数注入，只关注 shell 注入 | 已检查 | converter 参数路径已列为候选 |
| 是否误把普通回显当命令执行 | 已检查 | 无 confirmed，未作确认结论 |

## 9. 最终结论

| 状态 | 数量 | 编号 |
|---|---:|---|
| confirmed | 0 | - |
| candidate | 1 | CMD-EXEC-20260607-001 |
| blocked | 1 | CMD-EXEC-20260607-003 |
| false_positive | 0 | - |
| needs_environment | 1 | CMD-EXEC-20260607-002 |

```text
当前没有 confirmed。所有缺少动态证据或负向验证的发现均已降级。
```
