# Full Example

## 场景

本地授权项目包含头像上传、附件下载、预览接口、导入压缩包功能和对象存储 key 映射。已提供用户 A、用户 B、管理员、只读角色，以及租户 A、租户 B 的本地测试账号。

## 输入

```yaml
project_root: "D:\\projects\\local-oss-app"
local_base_url: "http://127.0.0.1:8080"
auth_contexts:
  anonymous: "no cookie"
  user_a: "tenant A normal user"
  user_b: "tenant A normal user"
  tenant_b_user: "tenant B normal user"
  admin: "tenant A admin"
  readonly: "tenant A readonly"
tenant_contexts:
  - tenant_a
  - tenant_b
test_marker_root: "D:\\projects\\local-oss-app\\security-markers\\file-boundary-9f3a"
evidence_output_dir: "D:\\projects\\local-oss-app\\security-evidence\\file-boundary-9f3a"
allowed_operations:
  - upload
  - download
  - preview
  - thumbnail
  - import
  - export
  - archive-extract
  - object-key-map
rollback_policy: "删除 marker 目录、删除测试上传记录、清理导入任务和导出缓存。"
```

## 验证矩阵片段

| endpoint | method | auth role | tenant | user | parameter | file operation | marker target | expected safe result | actual result | evidence | severity | status | next action |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| /api/avatar/upload | POST | user_a | tenant_a | A | filename, folder | upload | upload marker | 文件仅保存到用户头像目录 | 待执行 | request + response + fs | medium | not tested | 执行 baseline 与 folder 冲突请求 |
| /api/files/download | GET | user_b | tenant_a | B | id, path | read | user_a allowed marker | B 不应读取 A 文件 | 待执行 | request + response + marker | high | not tested | 执行 A/B 权限重放 |
| /api/preview | GET | readonly | tenant_a | readonly | key, url | preview | blocked marker | 不应读取 blocked marker | 待执行 | request + response + marker + fs | high | not tested | 测试 key/url 优先级 |
| /api/import/archive | POST | admin | tenant_a | admin | archive entry path | extract | upload marker | 解压不应越出导入目录 | 待执行 | request + response + fs before/after | high | not tested | 使用小型 marker 压缩包验证 |

## confirmed 示例

只有证据齐全时才能这样写：

```yaml
id: FBV-20260607-003
status: confirmed
vulnerability_type: "authorization-bypass"
endpoint: "GET /api/files/download"
auth_role: "普通用户 B"
tenant: "tenant_a"
request_sample: "GET /api/files/download?id=<user_a_file_id>&path=<redacted-marker-path>"
response_summary: "200，响应体包含 allowed-read-marker 的内容摘要"
marker_proof: "allowed-read-marker.txt digest matched evidence record"
filesystem_before: "marker path existed before request; digest abc..."
filesystem_after: "marker path unchanged after request; digest abc..."
log_evidence: "download controller log shows user_b request accepted for user_a file id"
positive_test: "user_a can read own marker file"
negative_test: "nonexistent id returns safe error without marker content"
blocked_test: "blocked marker traversal request returns 403"
impact_scope: "同租户非拥有者可通过 id/path 冲突读取他人附件 marker"
not_false_positive_reason: "业务预期为文件拥有者或授权角色可读；user_b 非拥有者且无共享记录"
not_static_guess_reason: "已执行 user_b 请求并匹配 marker 内容摘要"
minimal_fix: "下载接口在解析 path/key 前绑定 file id、owner、tenant、role，并忽略客户端 path 覆盖"
regression_test: "user_b 请求 user_a file id + path 冲突时必须返回 403 且不包含 marker"
rollback_status: "complete"
```

## 降级示例

```yaml
id: FBV-20260607-004
original_status: confirmed
reviewed_status: candidate
missing_proof:
  - tenant_b_user replay
  - filesystem before/after state
  - blocked control request
reason: "响应疑似包含 marker，但缺少租户矩阵、文件系统状态和 blocked 对照，不允许 confirmed。"
required_retest: "补齐 tenant_b_user、blocked marker、before/after 后重新分级。"
```
