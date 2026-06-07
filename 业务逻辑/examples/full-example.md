# 完整示例

> 示例内容为本地演示占位，用于展示报告结构、证据字段和降级逻辑。不得复制为真实项目结论。

# 业务逻辑漏洞动态验证报告

## 0. 报告元数据

| 字段 | 内容 |
|---|---|
| 项目名称 | local-demo-subscription |
| 本地项目路径 | `C:\lab\local-demo-subscription` |
| 验证日期 | `2026-06-07` |
| 授权边界 | 仅限本地测试环境 |
| 运行方式 | `npm run dev` |
| 测试数据库或快照 | `demo_test.sqlite`，验证前后均有快照 |
| 测试账号矩阵 | `member_a`、`owner_a`、`member_b` |
| 测试租户矩阵 | `tenant_a`、`tenant_b` |
| 日志来源 | `logs/app.log`、`logs/worker.log` |
| 禁止项确认 | 无真实支付、无真实数据破坏、无 DoS、无第三方访问 |

## 1. 项目业务暴露面总览

| 模块 | 业务对象 | 入口 | 角色 | 租户边界 | 关键状态 | 关键不变量 | 是否动态验证 | 风险等级 | 当前结论 | 证据编号 |
|---|---|---|---|---|---|---|---|---|---|---|
| Subscription | subscription | `POST /local/api/subscriptions/change-plan` | member | tenant_id from session | `trial/active/cancelled` | 套餐权益只能由服务端按当前 plan 计算 | yes | high | candidate | EV-CODE-001 |
| Coupon | coupon | `POST /local/api/coupons/redeem` | member | tenant_id + user_id | `unused/used/expired` | 优惠券只能使用一次 | yes | medium | blocked | EV-RESP-002, EV-DB-002 |
| PasswordReset | reset_token | `POST /local/api/password/reset` | user | user_id from token | `issued/used/expired` | 重置 token 只能使用一次 | yes | high | confirmed | EV-REQ-003, EV-RESP-003, EV-DB-003, EV-LOG-003, EV-CODE-003 |

## 2. Replay plan 节选

| 编号 | 业务对象 | 正常流程 | 被测试不变量 | 触发入口 | 前提 | 正向验证 | 负向验证 | 证据需求 | 计划结论 |
|---|---|---|---|---|---|---|---|---|---|
| BLV-20260607-001 | subscription | member 选择 plan，服务端计算权益 | 客户端不能提交 feature_flags | HTTP API | member_a / tenant_a / trial plan | 请求体加入 `feature_flags=[admin_export]` | owner 正常升级成功；member 非法字段应被忽略 | 请求、响应、DB、日志、代码 | candidate |
| BLV-20260607-002 | coupon | 未使用优惠券兑换后变 used | 优惠券只能使用一次 | HTTP API | member_a / tenant_a / coupon unused | 同一 coupon 重复提交两次 | 第二次应失败且 DB 无重复权益 | 请求、响应、DB、日志 | blocked |
| BLV-20260607-003 | reset_token | token 使用一次后失效 | 重置 token 只能使用一次 | HTTP API | user_a / issued token | 同一 token 连续重置两次 | 第二次应失败；旧 session 应失效 | 请求、响应、DB、日志、代码 | confirmed |

## 3. 已确认业务逻辑漏洞示例

### BLV-20260607-003：重置密码 token 可重复消费

| 字段 | 内容 |
|---|---|
| 严重性 | high |
| 影响范围 | 本地测试环境中用户账号密码重置流程 |
| 涉及角色 | 普通用户 |
| 涉及租户 | 无跨租户影响，已记录为单用户账号生命周期问题 |
| 涉及业务对象 | reset_token、user_session |
| 被破坏的不变量 | 密码重置 token 只能使用一次 |
| 正常流程 | 用户申请 reset token，使用一次后 token 状态变 `used`，旧 session 失效 |
| 异常绕过流程 | 同一 token 可第二次提交并再次改密 |
| 业务结果 | 第二次提交后 `users.password_hash` 再次变化；`reset_tokens.used_at` 未在第一次提交后写入 |

#### 证据摘要

| 证据编号 | 类型 | 内容 |
|---|---|---|
| EV-REQ-003 | 请求 | 同一 reset token 连续两次提交到本地 `/local/api/password/reset` |
| EV-RESP-003 | 响应 | 两次均返回 200 |
| EV-DB-003 | DB 前后 | 第二次后 `password_hash` 再次变化；token 未标记 consumed |
| EV-LOG-003 | 日志 | app.log 记录两次 reset success |
| EV-CODE-003 | 代码 | `ResetService.consume()` 未在事务内更新 token 状态 |

#### 负向验证

| 样本 | 预期 | 实际 | 结论 |
|---|---|---|---|
| 合法用户首次使用 token | 成功 | 成功 | pass |
| 第二次使用相同 token | 失败 | 成功 | fail，支撑 confirmed |
| 伪造 token | 失败 | 失败 | pass |

## 4. 候选漏洞示例

| 编号 | 标题 | 为什么可疑 | 当前缺少什么证据 | 如何最小化动态验证 | 为什么不能升级为 confirmed |
|---|---|---|---|---|---|
| BLV-20260607-001 | 订阅升级接口疑似接受隐藏 `feature_flags` 字段 | service 层合并 request body 到 subscription payload | 缺少 entitlement 表前后变化；日志未证明权益生效 | member_a 提交隐藏字段后查询 entitlement 表并访问导出接口 | 当前只有代码路径和响应，没有业务权益变化证据 |

## 5. 被阻断路径示例

| 编号 | 路径 | 看似危险点 | 阻断机制 | 阻断证据 | 最终结论 |
|---|---|---|---|---|---|
| BLV-20260607-002 | `POST /local/api/coupons/redeem` | 同一 coupon 重放 | DB 唯一约束 `coupon_redemptions(coupon_id,user_id)` 阻断第二次写入；响应 409；权益表无重复记录 | EV-RESP-002、EV-DB-002、EV-LOG-002、EV-CODE-002 | blocked |

## 6. 第一轮强制反思节选

| 反思项 | 检查结果 | 证据/补查动作 | 是否修正结论 |
|---|---|---|---|
| 是否把没有数据库变化的响应误判为漏洞 | 是 | BLV-20260607-001 缺少 entitlement 表变化证据 | 已从 confirmed 降级 candidate |
| 是否把 401/403 的失败路径误判为成功 | 否 | BLV-20260607-002 第二次请求为 409，DB 无重复写入 | 无 |
| 是否漏掉旧 token/session/API key | 否 | BLV-20260607-003 已验证旧 reset token 重放 | 保留 confirmed |

## 7. 第二轮偏门补挖节选

| 反向入口 | 检查对象 | 新增候选点 | replay plan | 动态验证结果 | 最终分级 |
|---|---|---|---|---|---|
| reset token | `reset_tokens.used_at` | token 未一次性消费 | BLV-20260607-003 | 动态复现成功，DB 与日志完整 | confirmed |
| feature flag | `subscriptions.feature_flags` | 客户端隐藏字段 | BLV-20260607-001 | 缺 entitlement 证据 | candidate |

## 8. 最终 confirmed 审判节选

| confirmed 编号 | 原严重性 | 20 项审判是否全通过 | 修正后分级 | 理由 |
|---|---|---|---|---|
| BLV-20260607-003 | high | yes | confirmed | 有请求、响应、DB 前后、日志、代码位置、负向验证；排除管理员正常能力、前端展示问题、测试接口误判 |

## 9. 示例说明

本示例展示三种结果：证据不足降级为 `candidate`，被唯一约束阻断写为 `blocked`，动态证据完整才保留 `confirmed`。
