# Basic Example：单个详情接口对象归属验证

## 场景

本地测试项目存在接口：

```text
GET http://127.0.0.1:3000/api/projects/{project_id}
```

测试资源：

| 资源 | 所属账号 | 所属租户 | marker |
|---|---|---|---|
| `project_a_001` | user_a | tenant_a | `marker_project_a_001` |
| `project_b_001` | user_b | tenant_b | `marker_project_b_001` |

## 输入

```text
project_path=D:\lab\demo-app
local_base_url=http://127.0.0.1:3000
evidence_dir=D:\lab\evidence\run-001
rollback_method=testing seed reset
```

## 暴露面矩阵条目

| 入口编号 | 入口位置 | 方法/协议 | 参数名 | 参数位置 | 资源类型 | 资源归属字段 | 当前登录角色 | 目标资源所属角色/租户 | 权限判断位置 | 是否存在服务端归属校验 | 是否需要动态验证 | 风险原因 | 证据路径 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| E-001 | `routes/api.*:/api/projects/{project_id}` | GET | project_id | path | project | owner_id, tenant_id | user_a | user_b / tenant_b | `ProjectController.show` | unknown | yes | 详情接口可能按 id 直接查询 | `evidence/project/routes.txt` |

## 正向验证

```bash
curl -s -i \
  -b "$USER_A_COOKIE" \
  "http://127.0.0.1:3000/api/projects/project_a_001" \
  -o "evidence/REQ-E001-user_a-positive.response.txt"
```

通过标准：响应为预期成功，并包含 `marker_project_a_001`。

## 反向与越界验证

```bash
curl -s -i \
  -b "$USER_A_COOKIE" \
  "http://127.0.0.1:3000/api/projects/project_b_001" \
  -o "evidence/REQ-E001-user_a-cross-tenant.response.txt"
```

预期安全结果：返回 401、403、404 或业务拒绝，且响应不得包含 `marker_project_b_001`。

## 归类规则

| 实际结果 | 归类 |
|---|---|
| 403 / 404 / 业务拒绝，无 tenant_b marker | blocked |
| 200，但响应为空或无 tenant_b marker | candidate 或 blocked；不得 confirmed |
| 200，响应包含 `marker_project_b_001`，且归属证明显示资源属于 tenant_b | confirmed |
| 请求失败、session 失效、无法证明资源归属 | candidate 或 not_run |

## confirmed 必填证据

| 证据 | 示例路径 |
|---|---|
| 正向请求 | `evidence/REQ-E001-user_a-positive.request.txt` |
| 正向响应 | `evidence/REQ-E001-user_a-positive.response.txt` |
| 越界请求 | `evidence/REQ-E001-user_a-cross-tenant.request.txt` |
| 越界响应 | `evidence/REQ-E001-user_a-cross-tenant.response.txt` |
| 资源归属证明 | `evidence/ownership/project_b_001.md` |
| 代码根因 | `evidence/code/project-show-owner-check-missing.md` |
| 回归脚本 | `evidence/regression/test-project-access.sh` |

## 示例结论

如果 user_a 请求 `project_b_001` 返回 200，响应包含 `marker_project_b_001`，且归属证明显示 `project_b_001` 属于 user_b / tenant_b，则标记为 `confirmed`。如果只返回 200 但没有 marker 或业务数据，不得标记为 `confirmed`。
