# 业务逻辑漏洞动态验证报告

> 只记录本地授权项目、本地测试环境、测试数据和可回滚验证结果。证据不足时不得写 `confirmed`。

## 0. 报告元数据

| 字段 | 内容 |
|---|---|
| 项目名称 | `<project>` |
| 本地项目路径 | `<path>` |
| 验证日期 | `<YYYY-MM-DD>` |
| 授权边界 | `仅限本地授权项目 / 测试环境 / 测试数据` |
| 运行方式 | `<command / container / service>` |
| 测试数据库或快照 | `<db / fixture / snapshot>` |
| 测试账号矩阵 | `<roles>` |
| 测试租户矩阵 | `<tenant A/B>` |
| 日志来源 | `<app log / worker log / queue log>` |
| 禁止项确认 | `无真实支付 / 无真实数据破坏 / 无 DoS / 无公网或敏感内网访问 / 无第三方攻击` |
| 结论分级集合 | `confirmed / candidate / blocked / false_positive / needs_environment` |

## 1. 项目业务暴露面总览

| 模块 | 业务对象 | 入口 | 角色 | 租户边界 | 关键状态 | 关键不变量 | 是否动态验证 | 风险等级 | 当前结论 | 证据编号 |
|---|---|---|---|---|---|---|---|---|---|---|
| `<module>` | `<object>` | `<HTTP/GraphQL/WebSocket/CLI/webhook/worker/admin/import/export>` | `<role>` | `<tenant rule>` | `<status>` | `<invariant>` | `<yes/no>` | `<critical/high/medium/low/info>` | `<classification>` | `<EV-*>` |

## 2. 项目理解结果

### 2.1 代码结构与运行入口

| 项 | 识别结果 | 来源文件/证据 | 是否影响验证 |
|---|---|---|---|
| 语言 | `<language>` | `<file>` | `<yes/no>` |
| 框架 | `<framework>` | `<file>` | `<yes/no>` |
| 入口文件 | `<entry>` | `<file>` | `<yes/no>` |
| 路由 | `<routes>` | `<file>` | `<yes/no>` |
| controller/service/model | `<components>` | `<file>` | `<yes/no>` |
| middleware | `<middleware>` | `<file>` | `<yes/no>` |
| worker/queue/cron | `<async>` | `<file>` | `<yes/no>` |

### 2.2 认证、角色和租户矩阵

| 维度 | 识别结果 | 代码/数据来源 | 动态验证状态 | 备注 |
|---|---|---|---|---|
| 认证方式 | `<session/JWT/OAuth/API key/magic link/code/webhook signature/admin token/service token>` | `<file/table>` | `<status>` | `<note>` |
| 角色 | `<anonymous/user/admin/owner/member/...>` | `<file/table>` | `<status>` | `<note>` |
| 租户 | `<tenant A/B>` | `<file/table>` | `<status>` | `<note>` |
| 旧凭证 | `<old token/session/API key>` | `<test data>` | `<status>` | `<note>` |

### 2.3 业务对象、状态机和不变量

| 业务对象 | 状态字段 | 合法状态流 | 非法状态跳转 | 业务不变量 | 来源 | replay plan 编号 |
|---|---|---|---|---|---|---|
| `<object>` | `<status field>` | `<normal flow>` | `<illegal transition>` | `<invariant>` | `<code/db/business rule>` | `<BLV-*>` |

### 2.4 业务流程图文本化

| 流程类型 | 入口 | 步骤 | 状态变化 | 证据 |
|---|---|---|---|---|
| 正常流程 | `<entry>` | `<steps>` | `<state changes>` | `<EV-*>` |
| 异常流程 | `<entry>` | `<steps>` | `<state changes>` | `<EV-*>` |
| 取消流程 | `<entry>` | `<steps>` | `<state changes>` | `<EV-*>` |
| 重试流程 | `<entry>` | `<steps>` | `<state changes>` | `<EV-*>` |
| 回滚流程 | `<entry>` | `<steps>` | `<state changes>` | `<EV-*>` |
| 管理员干预 | `<entry>` | `<steps>` | `<state changes>` | `<EV-*>` |
| webhook 异步回调 | `<entry>` | `<steps>` | `<state changes>` | `<EV-*>` |
| 队列补偿 | `<entry>` | `<steps>` | `<state changes>` | `<EV-*>` |

## 3. Replay plan 清单

| 编号 | 业务对象 | 正常业务流程 | 被测试不变量 | 攻击前提 | 触发入口 | 请求构造方式 | 正向验证 | 负向验证 | 证据需求 | 计划结论 |
|---|---|---|---|---|---|---|---|---|---|---|
| `<BLV-YYYYMMDD-001>` | `<object>` | `<normal>` | `<invariant>` | `<role/tenant/state/token/object id>` | `<entry>` | `<request>` | `<invalid request + DB/log checks>` | `<legal success / illegal fail / cross-tenant fail / replay fail / fixed fail>` | `<request/response/db/log/code/trace>` | `<classification>` |

## 4. 已确认业务逻辑漏洞

### `<BLV-YYYYMMDD-XXX>`：`<标题>`

| 字段 | 内容 |
|---|---|
| 严重性 | `<critical/high/medium/low>` |
| 影响范围 | `<scope>` |
| 涉及角色 | `<roles>` |
| 涉及租户 | `<tenant impact or none>` |
| 涉及业务对象 | `<objects>` |
| 被破坏的不变量 | `<invariant>` |
| 正常流程 | `<expected flow>` |
| 异常绕过流程 | `<actual bypass>` |
| 业务结果 | `<actual business state change>` |
| 结论依据 | `动态复现成功 + 证据完整` |

#### 动态复现步骤

1. `<prepare test data>`
2. `<send request or trigger local job>`
3. `<collect response>`
4. `<collect DB before/after>`
5. `<collect logs>`
6. `<run negative validation>`

#### 请求和响应

| 证据编号 | 类型 | 内容 | 脱敏说明 |
|---|---|---|---|
| `EV-REQ-*` | 请求 | `<method/path/body/headers-redacted>` | `<redaction>` |
| `EV-RESP-*` | 响应 | `<status/body>` | `<redaction>` |

#### 数据库前后变化

| 证据编号 | 表/集合 | 触发前 | 触发后 | 是否证明业务结果 |
|---|---|---|---|---|
| `EV-DB-BEFORE-* / EV-DB-AFTER-*` | `<table>` | `<before>` | `<after>` | `<yes/no>` |

#### 日志证据

| 证据编号 | 日志来源 | 关键内容 | 时间 |
|---|---|---|---|
| `EV-LOG-*` | `<app/worker/queue>` | `<log excerpt>` | `<timestamp>` |

#### 相关代码位置

| 证据编号 | 文件 | 行号/函数 | 作用 |
|---|---|---|---|
| `EV-CODE-*` | `<file>` | `<line/function>` | `<root cause>` |

#### 负向验证样本

| 样本 | 预期 | 实际 | 证据编号 | 结论 |
|---|---|---|---|---|
| 合法用户合法流程 | 成功 | `<actual>` | `<EV-*>` | `<pass/fail>` |
| 非法用户非法流程 | 失败 | `<actual>` | `<EV-*>` | `<pass/fail>` |
| 跨租户操作 | 失败 | `<actual>` | `<EV-*>` | `<pass/fail>` |
| 重放请求 | 失败 | `<actual>` | `<EV-*>` | `<pass/fail>` |
| 修复后回归 | 失败 | `<actual>` | `<EV-*>` | `<pass/fail>` |

#### 根因分析

`<root cause tied to code and invariant>`

#### 修复建议

`<server-side authorization / tenant isolation / state machine / transaction / idempotency / sensitive field allowlist / token revocation / audit log / regression tests>`

#### 修复后回归测试

`<exact regression checks>`

## 5. 候选漏洞

| 编号 | 标题 | 为什么可疑 | 当前缺少什么证据 | 如何最小化动态验证 | 为什么不能升级为 confirmed | 下一步条件 |
|---|---|---|---|---|---|---|
| `<BLV-*>` | `<title>` | `<static/dynamic signal>` | `<missing request/response/db/log/code/negative>` | `<minimal replay>` | `<reason>` | `<environment/data needed>` |

## 6. 被阻断路径

| 编号 | 路径 | 看似危险点 | 阻断机制 | 阻断证据 | 最终结论 |
|---|---|---|---|---|---|
| `<BLV-*>` | `<entry>` | `<risk>` | `<permission/state/schema/unique/transaction/idempotency/tenant/backend allowlist>` | `<EV-*>` | `blocked` |

## 7. false_positive

| 编号 | 原判断 | 不成立原因 | 排除证据 | 最终结论 |
|---|---|---|---|---|
| `<BLV-*>` | `<claim>` | `<admin normal ability / test-only path / frontend-only / failure response / config issue>` | `<EV-*>` | `false_positive` |

## 8. needs_environment

| 编号 | 需要的环境或数据 | 缺失导致不能判断的内容 | 已完成的非破坏性检查 | 最终结论 |
|---|---|---|---|---|
| `<BLV-*>` | `<missing env/data>` | `<impact>` | `<done>` | `needs_environment` |

## 9. 工程级修复建议

| 类别 | 修复项 | 落地点 | 回归测试 |
|---|---|---|---|
| 权限 | 后端强制权限校验 | `<middleware/service>` | `<role matrix>` |
| 租户 | 后端强制租户隔离 | `<query/worker/cache>` | `<tenant A/B>` |
| 状态机 | 服务端状态机 | `<state transition>` | `<illegal transition>` |
| 敏感字段 | 禁止客户端提交 role/status/price/tenant_id 等 | `<DTO/schema/allowlist>` | `<hidden param replay>` |
| 金额权益 | 金额、积分、余额由服务端计算 | `<pricing/ledger>` | `<negative/decimal/refund>` |
| webhook | 签名、timestamp、event_id 幂等 | `<handler>` | `<invalid/expired/replay>` |
| 事务幂等 | 订单、支付、退款使用事务、幂等 key、唯一约束 | `<db/service>` | `<duplicate/concurrent>` |
| 凭证 | token 一次性消费；状态变化撤销旧 session/token/API key | `<auth>` | `<old credential replay>` |
| 异步 | worker 保留 tenant context | `<queue/job>` | `<cross-tenant job>` |
| 缓存 | cache key 加 tenant_id | `<cache>` | `<cache pollution>` |
| 审计 | 关键业务操作增加审计日志 | `<audit log>` | `<log assertion>` |
| 回归 | 多角色、多租户、状态机、并发、重放测试 | `<test suite>` | `<CI/local>` |

## 10. 第一轮强制反思

| 反思项 | 检查结果 | 证据/补查动作 | 是否修正结论 |
|---|---|---|---|
| 是否只看 HTTP，漏 worker/cron/queue/webhook/CLI | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否只看前端，漏后端隐藏参数 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否只看单用户，漏多角色矩阵 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否只看单租户，漏跨租户影响 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否只看正常状态，漏非法状态跳转 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否漏异步补偿和失败重试 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否漏重复提交和重放 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否漏负数、小数、边界值、精度 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否漏旧 token/session/API key | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否漏禁用、删除、移除用户 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否漏管理员降权残留 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否漏缓存、队列、搜索索引、报表、导出租户隔离 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否把无 DB 变化的响应误判为漏洞 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否把 401/403 失败路径误判为成功 | `<yes/no>` | `<EV-*>` | `<yes/no>` |
| 是否存在无动态证据的 confirmed | `<yes/no>` | `<EV-*>` | `<yes/no>` |

## 11. 第二轮偏门补挖

| 反向入口 | 检查对象 | 新增候选点 | replay plan | 动态验证结果 | 最终分级 |
|---|---|---|---|---|---|
| 数据库字段 | 谁能写、谁会消费 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| status 字段 | 状态机缺口 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| price/amount/balance/points/quota | 客户端可控路径 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| tenant_id/org_id/owner_id | 跨租户路径 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| webhook handler | 幂等、签名、金额 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| worker job | 低权限投递高权限任务 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| admin 接口 | 普通用户间接触发 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| invite/reset/verify token | 复用和过期绕过 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| import/export/report | 越权和状态污染 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| cache key | 用户/租户污染 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| feature flag | 隐藏权限 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| plan/subscription | 低价高权 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| 审批流 | 自批、越级批、重复批 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| 取消/退款/回滚 | 权益残留 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |
| 异常处理/retry | 重复业务效果 | `<candidate>` | `<BLV-*>` | `<result>` | `<classification>` |

## 12. 最终 confirmed 审判

| confirmed 编号 | 原严重性 | 20 项审判是否全通过 | 修正后分级 | 降级或保留理由 |
|---|---|---|---|---|
| `<BLV-*>` | `<severity>` | `<yes/no>` | `<classification>` | `<reason>` |

## 13. 证据索引

| 证据编号 | 类型 | 来源 | 关联结论 | 文件/位置 |
|---|---|---|---|---|
| `EV-REQ-*` | request | `<local replay>` | `<BLV-*>` | `<path>` |
| `EV-RESP-*` | response | `<local replay>` | `<BLV-*>` | `<path>` |
| `EV-DB-BEFORE-*` | db-before | `<test db>` | `<BLV-*>` | `<query/snapshot>` |
| `EV-DB-AFTER-*` | db-after | `<test db>` | `<BLV-*>` | `<query/snapshot>` |
| `EV-LOG-*` | log | `<app/worker/queue>` | `<BLV-*>` | `<path>` |
| `EV-CODE-*` | code | `<file:line>` | `<BLV-*>` | `<path>` |
| `EV-TRACE-*` | screenshot/trace | `<frontend/local trace>` | `<BLV-*>` | `<path>` |

## 14. 最终结论摘要

| 分级 | 数量 | 说明 |
|---|---:|---|
| confirmed | `<n>` | 动态证据完整、可本地复现 |
| candidate | `<n>` | 静态或局部动态可疑，证据不足 |
| blocked | `<n>` | 路径存在但被后端机制阻断 |
| false_positive | `<n>` | 不成立 |
| needs_environment | `<n>` | 环境或测试数据不足 |
