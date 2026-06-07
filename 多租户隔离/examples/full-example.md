# Full Example

以下是虚构本地项目 `local-saas-demo` 的报告骨架，用于展示可接受结构，不代表真实漏洞。

## 0. 边界确认

| 项目 | 结果 |
|---|---|
| 目标项目路径 | C:\labs\local-saas-demo |
| API 基础地址 | http://127.0.0.1:3000 |
| 是否本地/本地容器/授权项目 | 是 |
| 是否使用测试数据库 | 是，local_saas_test |
| 是否只使用测试账号/测试租户/marker 数据 | 是 |
| 是否存在公网或第三方目标 | 否 |
| 是否存在 DoS/破坏性操作 | 否 |
| 写操作回滚方式 | marker 资源通过测试后台清理 |
| 结论 | safe-scope |

## 1. 项目租户隔离事实画像

- 项目启动方式：`docker compose up app db redis worker`
- 测试数据库位置：本地 docker postgres，库名 `local_saas_test`
- 认证入口：`POST /api/auth/login`、`GET /api/me`
- 租户模型：`organizations`、`organization_members`
- 租户识别来源：JWT claim `org_id`、header `X-Org-Id`、部分 body `org_id`
- 关键授权中间件：`src/middleware/auth.ts`、`src/policies/orgPolicy.ts`
- 高风险模块：documents、files、exports、audit_logs、api_keys
- 高风险参数：id、org_id、document_id、file_id、export_id、api_key_id
- 高风险表/模型：documents、files、exports、audit_logs、api_keys
- 高风险接口：`GET /api/documents/:id`、`POST /api/documents/search`、`GET /api/files/:id/preview`
- 暂时无法确认的点：GraphQL 不存在；WebSocket 组件未启用

## 2. 暴露面总表

| 模块 | 文件路径 | 路由/接口 | 方法 | 参数 | 认证方式 | 租户来源 | 授权检查位置 | 风险点 | 动态验证状态 |
|---|---|---|---|---|---|---|---|---|---|
| IDOR/BOLA | `src/routes/documents.ts` | `/api/documents/:id` | GET | id | JWT | JWT org_id | `orgPolicy.canReadDocument` | detail 按 id 查询 | blocked-by-control |
| 隐藏参数 | `src/routes/documents.ts` | `/api/documents/search` | POST | q, org_id, include_archived | JWT | body org_id + JWT org_id | `documentService.search` | body org_id 可污染过滤 | candidate |
| 文件 | `src/routes/files.ts` | `/api/files/:id/preview` | GET | id | JWT | JWT org_id | `filePolicy.canPreview` | preview 链路绕过 detail 鉴权 | confirmed |

## 3. 租户/角色/资源测试矩阵

| 租户 | 角色/凭证 | 用户或 token 标识 | 身份证明方式 | 状态 | 缺口 |
|---|---|---|---|---|---|
| Tenant A | A_admin | `a_admin@example.test` | `/api/me` 返回 `tenant_a` | ready | 无 |
| Tenant B | B_admin | `b_admin@example.test` | `/api/me` 返回 `tenant_b` | ready | 无 |

| marker 名称 | 资源类型 | 资源 ID | 所属租户 | 创建账号 | 归属证明 | 回滚/清理方式 |
|---|---|---|---|---|---|---|
| TENANT_A_FILE_MARKER | file | file_a_001 | A | A_admin | 创建响应 `tenant_a` | 删除 marker 文件 |
| TENANT_B_FILE_MARKER | file | file_b_001 | B | B_admin | 创建响应 `tenant_b` | 删除 marker 文件 |

## 4. 动态验证执行记录

| 测试编号 | 候选编号 | 测试类型 | 执行账号 | 执行租户 | 目标资源 | 目标归属 | 请求摘要 | 响应摘要 | 状态 | 证据路径 | 结论依据 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T-001 | CAND-002 | 正向 | A_admin | A | file_a_001 | A | `GET /api/files/file_a_001/preview` | 200，A marker | confirmed | evidence/T-001.har | 正向成功 |
| T-002 | CAND-002 | 反向 | A_admin | A | file_b_001 | B | `GET /api/files/file_b_001/preview` | 200，B marker | confirmed | evidence/T-002.har | 反向返回 B marker |

## 5. confirmed 漏洞列表

| 漏洞编号 | 漏洞名称 | 严重等级 | 影响租户 | 影响角色 | 影响资源 | 状态 |
|---|---|---|---|---|---|---|
| TI-001 | 文件预览接口缺少资源租户归属校验 | High | Tenant B | A_admin | B 文件 marker | confirmed |

## 6. high/critical 重点漏洞详情

### TI-001

【漏洞名称】文件预览接口缺少资源租户归属校验

【严重等级】High

【影响租户】Tenant B

【影响角色】A_admin

【影响资源】`TENANT_B_FILE_MARKER`，资源 ID `file_b_001`

【资源归属证明】B_admin 创建响应显示 `tenant_id=tenant_b`，证据 `evidence/create-file-b.har`。

【请求身份证明】A_admin 调用 `/api/me` 返回 `tenant_id=tenant_a`，证据 `evidence/me-a-admin.har`。

【正向请求】

```http
GET /api/files/file_a_001/preview HTTP/1.1
Host: 127.0.0.1:3000
Authorization: Bearer <redacted>
```

【正向响应摘要】

```json
{"status":200,"file_id":"file_a_001","marker":"TENANT_A_FILE_MARKER","tenant_id":"tenant_a"}
```

【越权请求】

```http
GET /api/files/file_b_001/preview HTTP/1.1
Host: 127.0.0.1:3000
Authorization: Bearer <redacted>
```

【越权响应摘要】

```json
{"status":200,"file_id":"file_b_001","marker":"TENANT_B_FILE_MARKER","tenant_id":"tenant_b"}
```

【为什么这是租户隔离漏洞】A_admin 属于 tenant_a，目标文件属于 tenant_b，反向请求返回 B marker。

【为什么不是预期权限】A_admin 不是平台管理员，不属于 tenant_b，B 未共享该文件。

【复现步骤】1. B_admin 创建 B marker 文件；2. A_admin 证明身份为 tenant_a；3. A_admin 请求 B 文件 preview；4. 响应包含 B marker。

【最小化 PoC】

```bash
curl -sS 'http://127.0.0.1:3000/api/files/file_b_001/preview' -H 'Authorization: Bearer <redacted>'
```

【涉及文件】`src/routes/files.ts`、`src/services/filePreviewService.ts`、`src/repositories/fileRepository.ts`

【根因代码】`fileRepository.findById(fileId)` 只按 file_id 查询，未加 current tenant。

【修复建议】preview/thumbnail/download/export 统一执行 `file_id + current_tenant_id` 归属校验。

【回归测试建议】A_admin 请求 B file preview 返回 403/404，响应不含 `TENANT_B_FILE_MARKER`。

【证据文件路径】`evidence/T-001.har`、`evidence/T-002.har`

## 7. candidate 漏洞列表

### CAND-003

【候选名称】搜索接口接受 body.org_id 和 include_archived

【代码位置】`src/routes/documents.ts`、`src/services/documentSearchService.ts`

【怀疑原因】后端 DTO 接受 `org_id`，前端正常请求不传该字段。

【缺少什么动态证据】未执行 A_owner 传 B org_id 搜索 B marker 的反向请求。

【下一步验证请求】

```http
POST /api/documents/search HTTP/1.1
Host: 127.0.0.1:3000
Authorization: Bearer <redacted>
Content-Type: application/json

{"q":"TENANT_B_PRIVATE_DOC_MARKER","org_id":"tenant_b","include_archived":true}
```

【需要的账号/租户/marker】A_owner、tenant_a、tenant_b、TENANT_B_PRIVATE_DOC_MARKER

【预期成功结果】响应包含 `TENANT_B_PRIVATE_DOC_MARKER` 时升级 confirmed。

【预期阻断结果】403、404、空数组、或仅返回 tenant_a 数据。

【不能确认的原因】尚无动态响应证据。

## 8. 同族漏洞拓展结果

- 根因模式：文件接口按 file_id 查询，缺少 current tenant 约束。
- 命中的文件：`src/routes/files.ts`、`src/services/filePreviewService.ts`、`src/services/fileDownloadService.ts`
- 命中的接口：preview、thumbnail、download
- 已动态验证 confirmed：preview
- 仍为 candidate：thumbnail、download
- 下一步测试计划：A_admin 访问 B thumbnail/download marker。

| 原漏洞 | 根因模式 | 同族文件 | 同族接口 | 动态验证请求 | 结果 | 严重性 | 证据 |
|---|---|---|---|---|---|---|---|
| TI-001 | file_id 查询缺 tenant | `src/routes/files.ts` | `/api/files/:id/thumbnail` | A_admin GET B thumbnail | candidate | High | 待执行 |
| TI-001 | file_id 查询缺 tenant | `src/routes/files.ts` | `/api/files/:id/download` | A_admin GET B download | candidate | High | 待执行 |

## 12. 本轮审计可靠性自我评估

评级：B。核心 HTTP API 已动态验证；WebSocket、异步导出、API Key 未覆盖。

## 13. 第二轮反向审判复核结果

TI-001 保持 confirmed；thumbnail/download 保持 candidate；CAND-003 保持 candidate。距离 A 缺 WebSocket、异步导出、API Key、文件下载动态验证。
