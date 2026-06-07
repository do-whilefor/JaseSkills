# Full Example：完整本地对象访问控制动态审计运行

## 输入摘要

| 项目 | 示例值 |
|---|---|
| project_path | `D:\lab\invoice-app` |
| local_base_url | `http://127.0.0.1:8080` |
| evidence_dir | `D:\lab\evidence\invoice-run-001` |
| rollback_method | `docker compose exec app php artisan migrate:fresh --seed --env=testing` |
| 账号 | user_a、user_b、manager_a、admin_local、anonymous |
| 租户 | tenant_a、tenant_b |

## 阶段 0：运行边界

```text
目标为 127.0.0.1，本地 docker compose 服务。
只使用 testing seed 创建的 marker 数据。
写操作仅作用于 marker_invoice_* 测试记录。
证据目录可写。
```

## 阶段 1：项目识别

| 项目 | 结果 | 证据路径 |
|---|---|---|
| 语言/框架 | Laravel | `evidence/project/framework.txt` |
| 路由 | `routes/api.php`, `routes/web.php` | `evidence/project/routes.txt` |
| 前端 JS | `public/build/assets/*.js` | `evidence/project/frontend-js.txt` |
| 模型 | `app/Models/*.php` | `evidence/project/models.txt` |
| 权限 | `app/Policies`, `app/Http/Middleware` | `evidence/project/authz.txt` |

## 阶段 2：暴露面矩阵节选

| 入口编号 | 入口位置 | 方法/协议 | 参数名 | 参数位置 | 资源类型 | 资源归属字段 | 当前登录角色 | 目标资源所属角色/租户 | 权限判断位置 | 是否存在服务端归属校验 | 是否需要动态验证 | 风险原因 | 证据路径 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E-001 | `routes/api.php:/api/invoices/{id}` | GET | id | path | invoice | tenant_id, owner_id | user_a | tenant_b | `InvoiceController@show` | unknown | yes | 详情接口可能只用 `Invoice::find($id)` | `evidence/project/routes.txt` |
| E-002 | `routes/api.php:/api/invoices/export` | POST | invoice_ids | JSON body | invoice | tenant_id | user_a | tenant_b | `ExportController@invoice` | unknown | yes | 批量导出可能未逐项校验 | `evidence/project/routes.txt` |
| E-003 | `public/build/app.js` | GET | task_id | query | export_task | owner_id, tenant_id | user_a | tenant_b | `ExportTaskController@result` | unknown | yes | 异步任务结果可能未绑定用户 | `evidence/project/frontend-js.txt` |

## 阶段 3：测试数据

| 资源编号 | 资源类型 | 资源 ID | owner_id | tenant_id | org_id | visibility | status | marker | 归属证明路径 |
|---|---|---|---|---|---|---|---|---|---|
| R-A-001 | invoice | inv_a_001 | user_a | tenant_a | org_a | private | draft | marker_inv_a_001 | `evidence/ownership/inv_a_001.md` |
| R-A-002 | invoice | inv_a_002 | user_a | tenant_a | org_a | private | issued | marker_inv_a_002 | `evidence/ownership/inv_a_002.md` |
| R-B-001 | invoice | inv_b_001 | user_b | tenant_b | org_b | private | issued | marker_inv_b_001 | `evidence/ownership/inv_b_001.md` |
| R-B-002 | invoice | inv_b_002 | user_b | tenant_b | org_b | private | paid | marker_inv_b_002 | `evidence/ownership/inv_b_002.md` |

## 阶段 4：动态验证结果节选

| 验证编号 | 入口编号 | 验证类型 | 测试账号 | 目标资源 | 替换字段 | 预期安全结果 | 实际结果 | 分类 | 执行状态 | 证据路径 |
|---|---|---|---|---|---|---|---|---|---|---|
| V-001 | E-001 | 正向 | user_a | inv_a_001 | id | 200 且返回 marker_inv_a_001 | 200 且返回 marker | blocked baseline | done | `evidence/requests/V-001.*` |
| V-002 | E-001 | 越界 | user_a | inv_b_001 | id | 403/404 或业务拒绝 | 403，无 marker_inv_b_001 | blocked | done | `evidence/requests/V-002.*` |
| V-003 | E-002 | 越界 | user_a | inv_b_001 | invoice_ids[0] | 403/404 或业务拒绝 | 200，导出文件含 marker_inv_b_001 | confirmed | done | `evidence/requests/V-003.*` |
| V-004 | E-003 | 越界 | user_a | task_b_001 | task_id | 403/404 或业务拒绝 | 未创建 tenant_b 导出任务 fixture | candidate | not_run | `evidence/not-run/V-004.md` |

## confirmed 示例

### CONF-001

| 字段 | 内容 |
|---|---|
| 漏洞编号 | CONF-001 |
| 影响资源 | invoice 导出文件 |
| 受影响接口 | `POST /api/invoices/export` |
| 受影响角色 | 普通用户 user_a |
| 越界方向 | user_a / tenant_a 导出 user_b / tenant_b 的 invoice |
| 最小复现步骤 | 1. user_a 登录。2. 发送导出请求，body 中把 `invoice_ids` 替换为 `inv_b_001`。3. 下载导出结果。4. 导出文件包含 `marker_inv_b_001`。 |
| 原始请求证据路径 | `evidence/requests/V-003.request.txt` |
| 原始响应关键片段 | `200 OK`, `export_task_id=task_abc`; 导出文件中含 `marker_inv_b_001` |
| 测试账号说明 | user_a 属于 tenant_a，普通用户 |
| 测试资源归属证明 | `evidence/ownership/inv_b_001.md` 证明 inv_b_001 属于 user_b / tenant_b |
| 代码根因位置 | `app/Http/Controllers/ExportController.php:42` 使用 `Invoice::whereIn('id', $ids)`，未添加 tenant/user 过滤 |
| 为什么前端限制无效或不足 | 前端列表只展示 tenant_a invoice，但后端接受任意 `invoice_ids` |
| 为什么服务端校验缺失 | 服务端未对 `invoice_ids` 每个 id 做 tenant_id 与 owner/role 校验 |
| 可复现脚本或 curl | `evidence/regression/repro-conf-001.sh` |
| 修复建议 | 在导出查询中加入 tenant scope，并逐项拒绝无权限 invoice_id；导出任务绑定 requester_id 和 tenant_id |
| 修复后验证方法 | user_a 重放同一请求，应返回 403/404/业务拒绝，导出文件不得包含 `marker_inv_b_001` |
| 严重程度 | high |
| 严重程度理由 | 普通用户可导出其他租户非公开资源，符合 TXT 高影响条件 |

## 反向审计节选

| 序号 | 问题 | 回答 | 证据路径 | 是否需要补测 |
|---:|---|---|---|---|
| 1 | 是否漏掉 JS/chunk/source map/移动端/旧版/管理端 API | 初轮只覆盖 UI 和路由表；补查前端 chunk 后发现 E-003 task result | `evidence/project/frontend-js.txt` | 是，E-003 not_run |
| 8 | 是否检查批量接口逐项权限 | 已检查 E-002，发现 CONF-001 | `evidence/requests/V-003.*` | 否 |
| 9 | 是否检查任务 id/token 绑定 | task fixture 缺失，未执行 | `evidence/not-run/V-004.md` | 是 |

## 遗漏路径清单节选

| 漏掉的入口 | 为什么第一轮会漏 | 需要补测的具体请求 | 需要使用哪个测试账号 | 需要替换哪个对象引用字段 | 预期安全结果 | 如果失败代表什么缺陷 | 执行状态 | 证据文件路径 |
|---|---|---|---|---|---|---|---|---|
| `GET /api/export/result?task_id=` | 初轮只测同步导出，未创建异步任务 fixture | `GET /api/export/result?task_id=task_b_001` | user_a | task_id | 403/404 或业务拒绝 | 异步任务结果未绑定 requester 或 tenant | not_run | `evidence/not-run/V-004.md` |
| `PATCH /api/invoices/{id}` body owner_id | 初轮只测 GET 详情 | `PATCH /api/invoices/inv_a_001` body `owner_id=user_b` | user_a | owner_id | 拒绝或忽略 owner_id | 后端接受前端未暴露字段导致资源转移 | done | `evidence/requests/V-005.*` |

## 非常规路径补测节选

| 路径类型 | 具体入口 | 账号 | 替换字段 | 预期安全结果 | 真实执行结果 | 执行状态 | 证据路径 |
|---|---|---|---|---|---|---|---|
| 批量对象接口逐项校验 | `POST /api/invoices/export` | user_a | `invoice_ids[]` | 拒绝 tenant_b id | 200 且导出 marker_inv_b_001 | done | `evidence/requests/V-003.*` |
| 后端接受未暴露字段 | `PATCH /api/invoices/{id}` | user_a | `owner_id` | 拒绝或忽略 | 422 字段不允许 | done | `evidence/requests/V-005.*` |
| 异步任务结果查询 | `GET /api/export/result` | user_a | `task_id` | 拒绝 tenant_b task | 缺 task fixture | not_run | `evidence/not-run/V-004.md` |

## 回归脚本模板

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${LOCAL_BASE_URL:?}"
: "${USER_A_COOKIE:?}"
: "${TENANT_B_INVOICE_ID:?}"
: "${EVIDENCE_DIR:?}"

mkdir -p "$EVIDENCE_DIR/regression"

curl -s -i \
  -b "$USER_A_COOKIE" \
  -H 'Content-Type: application/json' \
  -X POST "$LOCAL_BASE_URL/api/invoices/export" \
  --data "{\"invoice_ids\":[\"$TENANT_B_INVOICE_ID\"]}" \
  -o "$EVIDENCE_DIR/regression/export-cross-tenant.response.txt"

if grep -q 'marker_inv_b_001' "$EVIDENCE_DIR/regression/export-cross-tenant.response.txt"; then
  echo 'FAIL: cross-tenant marker leaked'
  exit 1
fi

echo 'PASS: cross-tenant export blocked or no marker leaked'
```
