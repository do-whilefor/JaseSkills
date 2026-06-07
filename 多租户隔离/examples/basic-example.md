# Basic Example

## 输入

```text
使用 tenant-isolation-dynamic-validation Skill。
项目路径：C:\labs\local-saas-demo
API 地址：http://127.0.0.1:3000
数据库：本地 docker postgres，库名 local_saas_test
账号：A_owner/A_admin/A_member/A_viewer/B_owner/B_admin/B_member/B_viewer，凭证已脱敏
限制：只能使用 marker 数据；不允许删除真实业务数据；可以创建和更新 marker 资源。
```

## 合格输出片段

```markdown
## 0. 边界确认

| 项目 | 结果 |
|---|---|
| 目标项目路径 | C:\labs\local-saas-demo |
| API 基础地址 | http://127.0.0.1:3000 |
| 是否本地/本地容器/授权项目 | 是，本地项目 |
| 是否使用测试数据库 | 是，local_saas_test |
| 是否只使用测试账号/测试租户/marker 数据 | 是 |
| 是否存在公网或第三方目标 | 否 |
| 是否存在 DoS/破坏性操作 | 否 |
| 结论 | safe-scope |

## 1. 项目租户隔离事实画像

- 项目启动方式：`npm run dev`，来源 `package.json`
- 测试数据库位置：docker postgres `local_saas_test`，连接串已脱敏
- 认证入口：`POST /api/auth/login`、`GET /api/me`
- 租户模型：`organizations` 表，代码中使用 `org_id`
- 租户识别来源：JWT claim `org_id`、Header `X-Org-Id`、部分 body `org_id`
- 关键授权中间件：`src/middleware/auth.ts`、`src/policies/orgPolicy.ts`
- 高风险模块：documents、files、exports、audit_logs
- 高风险参数：id、org_id、document_id、file_id、export_id
- 高风险表/模型：documents、files、exports、audit_logs
- 高风险接口：`GET /api/documents/:id`、`GET /api/files/:id/preview`
- 暂时无法确认的点：WebSocket 未启动，实时通知未覆盖
```

## 不合格输出

```markdown
项目存在租户越权风险，应检查接口权限。
```

不合格原因：没有事实画像、矩阵、marker、具体接口、动态请求、证据分流、第二轮反向审判。
