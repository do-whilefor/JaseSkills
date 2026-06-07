# 基础示例

> 本示例只演示如何按 Skill 分级，不代表真实漏洞证据。

## 输入

```text
项目路径：C:\lab\demo-shop
授权边界：仅限本地 demo-shop 测试环境
启动方式：npm run dev
测试数据库：demo_shop_test，运行前已快照
测试账号：user_a(member)、user_b(member)、owner_a(owner)
测试租户：tenant_a、tenant_b
日志位置：C:\lab\demo-shop\logs\app.log
禁止项：不访问公网，不调用真实支付，不做压测，不破坏真实数据
```

## 执行要点

1. 确认项目能启动，数据库是测试库。
2. 识别订单接口、权限中间件、订单状态字段和租户字段。
3. 发现 `POST /api/orders/{id}/cancel` 读取 `order_id`，静态上未看到显式 `tenant_id` 校验。
4. 生成 replay plan：`user_a` 尝试取消 `tenant_b` 的订单。
5. 执行动态验证并记录请求、响应、DB 前后、日志和代码位置。

## 正确输出节选

### 项目业务暴露面总览

| 模块 | 业务对象 | 入口 | 角色 | 租户边界 | 关键状态 | 关键不变量 | 是否动态验证 | 风险等级 | 当前结论 | 证据编号 |
|---|---|---|---|---|---|---|---|---|---|---|
| Order | order | `POST /api/orders/{id}/cancel` | member | order.tenant_id 必须等于 session.tenant_id | `pending/paid/cancelled` | A 租户不能影响 B 租户订单 | yes | medium | blocked | EV-RESP-001, EV-DB-001, EV-LOG-001 |

### 被阻断路径

| 编号 | 路径 | 看似危险点 | 阻断机制 | 阻断证据 | 最终结论 |
|---|---|---|---|---|---|
| BLV-20260607-001 | `POST /api/orders/{tenant_b_order}/cancel` | user_a 传入 tenant_b 的 order_id | 后端返回 403；DB 中订单状态未变化；日志记录 tenant mismatch | EV-RESP-001, EV-DB-001, EV-LOG-001 | blocked |

## 禁止的错误写法

```text
发现订单取消接口未检查 tenant_id，确认存在跨租户取消订单漏洞。
```

该写法失败原因：只有静态可疑点，动态结果显示被后端阻断。正确结论是 `blocked`；如果无法运行动态验证，则是 `candidate` 或 `needs_environment`。
