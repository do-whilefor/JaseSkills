# 本地对象引用访问控制动态验证报告

## 1. 运行边界

| 字段 | 值 | 证据路径 |
|---|---|---|
| project_path |  |  |
| local_base_url |  |  |
| run_id |  |  |
| evidence_dir |  |  |
| rollback_method |  |  |
| 是否确认本地授权 |  |  |
| 是否访问公网目标 | 否 |  |
| 是否使用真实隐私数据 | 否 |  |
| 是否只使用测试账号/marker 数据 |  |  |

## 2. 项目识别结果

| 项目 | 结果 | 证据路径 |
|---|---|---|
| 语言/框架 |  |  |
| 后端入口文件 |  |  |
| 路由注册位置 |  |  |
| GraphQL schema/resolver |  |  |
| WebSocket/RPC 入口 |  |  |
| 前端 JS / chunk / source map |  |  |
| 移动端/管理端/内部端入口 |  |  |
| 数据库模型位置 |  |  |
| 权限中间件 / policy / guard |  |  |
| ORM / repository / service 校验位置 |  |  |

## 3. 访问控制暴露面矩阵

| 入口编号 | 入口位置 | 方法/协议 | 参数名 | 参数位置 | 资源类型 | 资源归属字段 | 当前登录角色 | 目标资源所属角色/租户 | 权限判断位置 | 是否存在服务端归属校验 | 是否需要动态验证 | 风险原因 | 证据路径 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E-001 |  |  |  | path/query/body/form-data/header/cookie/GraphQL variable/WebSocket payload |  | owner_id/tenant_id/org_id/... |  |  |  | yes/no/unknown | yes/no |  |  |

## 4. 测试身份

| 账号 | 角色 | 租户 | session/认证证据路径 | 说明 |
|---|---|---|---|---|
| user_a | 普通用户 | tenant_a |  |  |
| user_b | 普通用户 | tenant_b |  |  |
| manager_a | 管理角色 | tenant_a |  |  |
| admin_local | 本地测试管理员 | local/admin |  |  |
| anonymous | 未登录 | 无 |  |  |

## 5. 测试资源与归属证明

| 资源编号 | 资源类型 | 资源 ID | owner_id | tenant_id | org_id | visibility | status | marker | 归属证明路径 | 回滚证据路径 |
|---|---|---|---|---|---|---|---|---|---|---|
| R-A-001 |  |  | user_a | tenant_a |  |  |  |  |  |  |
| R-A-002 |  |  | user_a | tenant_a |  |  |  |  |  |  |
| R-B-001 |  |  | user_b | tenant_b |  |  |  |  |  |  |
| R-B-002 |  |  | user_b | tenant_b |  |  |  |  |  |  |

## 6. 真实请求清单

| 请求编号 | 入口编号 | 来源 | 方法/协议 | 路径/事件 | 对象引用字段 | 参数位置 | 原始账号 | 可重放 | 证据路径 |
|---|---|---|---|---|---|---|---|---|---|
| REQ-001 | E-001 | UI/HAR/JS/route/log/test |  |  |  |  |  | yes/no |  |

## 7. 动态验证结果摘要

| 验证编号 | 入口编号 | 验证类型 | 测试账号 | 目标资源 | 替换字段 | 预期安全结果 | 实际结果 | 分类 | 执行状态 | 证据路径 |
|---|---|---|---|---|---|---|---|---|---|---|
| V-001 | E-001 | positive/reverse/cross-boundary/blocking |  |  |  | 401/403/404/业务拒绝或预期成功 |  | confirmed/blocked/candidate/false_positive | done/not_run/blocked/failed |  |

## 8. confirmed

### CONF-001

| 字段 | 内容 |
|---|---|
| 漏洞编号 | CONF-001 |
| 影响资源 |  |
| 受影响接口 |  |
| 受影响角色 |  |
| 越界方向 | 例如 user_a / tenant_a 访问 user_b / tenant_b |
| 最小复现步骤 | 1.  2.  3.  |
| 原始请求 | 证据路径：`evidence/...request.txt`；不得只写口头描述 |
| 原始响应关键片段 | 状态码、marker、关键字段；不得包含真实隐私 |
| 测试账号说明 |  |
| 测试资源归属证明 | 证据路径：`evidence/ownership/...md` |
| 代码根因位置 | 文件路径、函数、行号或定位依据；未定位写 `unknown` 并说明原因 |
| 为什么前端限制无效或不足 |  |
| 为什么服务端校验缺失 |  |
| 可复现脚本或 curl | 证据路径或命令；必须限定本地 base URL |
| 修复建议 | 具体到校验位置、归属字段、拒绝策略、回归点 |
| 修复后验证方法 | 重放同请求，预期 401/403/404/业务拒绝且无 marker 泄露 |
| 严重程度与理由 | low/medium/high；high 必须满足 TXT 高影响条件 |

## 9. blocked

| 编号 | 入口 | 测试账号 | 目标资源 | 阻断状态 | 预期安全结果 | 证据路径 |
|---|---|---|---|---|---|---|
| BLK-001 |  |  |  | 401/403/404/业务拒绝 |  |  |

## 10. candidate

| 编号 | 入口 | 可疑原因 | 缺失证据 | 不得 confirmed 的原因 | 下一步验证 | 证据路径 |
|---|---|---|---|---|---|---|
| CAN-001 |  |  |  |  |  |  |

## 11. false_positive

| 编号 | 入口 | 初始怀疑 | 排除原因 | 证据路径 |
|---|---|---|---|---|
| FP-001 |  |  |  |  |

## 12. 反向审计回答

| 序号 | 问题 | 回答 | 证据路径 | 是否需要补测 |
|---:|---|---|---|---|
| 1 | 是否只测 UI 接口，漏掉 JS/chunk/source map/移动端/旧版/管理端 API |  |  | yes/no |
| 2 | 是否只测 GET，漏掉 POST/PUT/PATCH/DELETE/export/download/preview/import/async task |  |  |  |
| 3 | 是否只替换 path id，漏掉 query/body/form-data/header/cookie/GraphQL variable/WebSocket payload |  |  |  |
| 4 | 是否只测 user_a 与 user_b，漏掉租户、manager、anonymous |  |  |  |
| 5 | 是否验证资源归属证明，而不是只看状态码 |  |  |  |
| 6 | 是否把 200 空响应误判为越界成功 |  |  |  |
| 7 | 是否把管理员正常权限误判为缺陷 |  |  |  |
| 8 | 是否检查批量接口每一个 id 的逐项权限校验 |  |  |  |
| 9 | 是否检查缓存 key、异步任务 id、导出任务 id、下载 token、分享 token 绑定关系 |  |  |  |
| 10 | 是否检查 ORM include/populate/preload 关联泄露 |  |  |  |
| 11 | 是否检查前端未暴露字段 tenant_id/owner_id/role/status/created_by/assignee_id |  |  |  |
| 12 | 是否检查 GraphQL nested resolver、alias、batching、node(id) |  |  |  |
| 13 | 是否检查 WebSocket room、topic、subscription、message history |  |  |  |
| 14 | 是否检查软删除、历史版本、审计日志、通知中心、搜索建议、统计聚合接口 |  |  |  |
| 15 | 是否有完整请求、响应、账号、资源归属、代码根因、修复建议、回归测试证据 |  |  |  |

## 13. 遗漏路径清单

| 漏掉的入口 | 为什么第一轮会漏 | 需要补测的具体请求 | 需要使用哪个测试账号 | 需要替换哪个对象引用字段 | 预期安全结果 | 如果失败代表什么缺陷 | 执行状态 | 证据文件路径 |
|---|---|---|---|---|---|---|---|---|
|  |  |  | user_a/user_b/manager_a/admin_local/anonymous |  | 401/403/404/业务拒绝 |  | done/not_run/blocked/failed |  |

## 14. 非常规路径补测结果

| 路径类型 | 具体入口 | 账号 | 替换字段 | 预期安全结果 | 真实执行结果 | 执行状态 | 证据路径 |
|---|---|---|---|---|---|---|---|
| 旧/废弃/兼容/移动/admin/internal 接口 |  |  |  |  |  |  |  |
| 前端未使用但后端注册路由 |  |  |  |  |  |  |  |
| 自动生成 CRUD |  |  |  |  |  |  |  |
| REST 与 GraphQL 权限一致性 |  |  |  |  |  |  |  |
| API 直接请求绕过页面权限 |  |  |  |  |  |  |  |
| 列表与详情/导出/下载/统计差异 |  |  |  |  |  |  |  |
| 创建与更新归属字段差异 |  |  |  |  |  |  |  |
| 批量对象逐项校验 |  |  |  |  |  |  |  |
| 子资源/附件/评论/消息/历史版本 |  |  |  |  |  |  |  |
| include/expand/populate 关联泄露 |  |  |  |  |  |  |  |
| 异步任务结果查询 |  |  |  |  |  |  |  |
| method override/content-type/multipart/JSON merge patch |  |  |  |  |  |  |  |
| 已知 UUID 对象引用 |  |  |  |  |  |  |  |
| 缓存复用 |  |  |  |  |  |  |  |
| 事务/状态机/审批/邀请/分享/绑定流程 |  |  |  |  |  |  |  |

## 15. 修复优先级

| 优先级 | 问题 | 理由 | 修复位置 | 回归验证 |
|---|---|---|---|---|
| P0/P1/P2 |  |  |  |  |

## 16. 回归测试脚本

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${LOCAL_BASE_URL:?must be local}"
: "${USER_A_COOKIE:?}"
: "${TENANT_B_RESOURCE_ID:?}"
: "${EVIDENCE_DIR:?}"

mkdir -p "$EVIDENCE_DIR/regression"

curl -s -i \
  -b "$USER_A_COOKIE" \
  "$LOCAL_BASE_URL/<replace-path>/$TENANT_B_RESOURCE_ID" \
  -o "$EVIDENCE_DIR/regression/cross-boundary.response.txt"

if grep -q 'marker_tenant_b' "$EVIDENCE_DIR/regression/cross-boundary.response.txt"; then
  echo 'FAIL: cross-boundary marker leaked'
  exit 1
fi

echo 'PASS: request blocked or no cross-boundary marker returned'
```

## 17. 结论限制

| 限制项 | 内容 |
|---|---|
| 未执行项 |  |
| blocked 项 |  |
| failed 项 |  |
| 不能下结论的原因 |  |
| 不得写成 confirmed 的项目 |  |
