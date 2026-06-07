# File Boundary Verify Report

## 1. 项目文件处理攻击面总览

| 项目项 | 内容 | 证据来源 | 状态 |
|---|---|---|---|
| project_root |  |  | confirmed / unknown |
| local_base_url |  |  | confirmed / unavailable |
| language |  |  | confirmed / unknown |
| framework |  |  | confirmed / unknown |
| upload libraries |  |  | confirmed / none found / unknown |
| storage adapters |  |  | confirmed / none found / unknown |
| object storage |  |  | confirmed / none found / unknown |
| static serving |  |  | confirmed / none found / unknown |
| import/export modules |  |  | confirmed / none found / unknown |
| preview/convert/thumbnail workers |  |  | confirmed / none found / unknown |

## 2. 上传入口清单

| id | endpoint | method | handler/source | auth required | tenant scoped | parameters | storage target | follow-up access | status | evidence |
|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  | yes/no/unknown | yes/no/unknown |  |  | static/download/preview/convert/none | candidate/not tested/confirmed |  |

## 3. 读取入口清单

| id | endpoint | method | operation | handler/source | accepted identifiers | hidden parameters | auth required | tenant scoped | status | evidence |
|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  | download/preview/thumbnail/convert/export/log/static/object-key |  | id/path/key/url/name |  | yes/no/unknown | yes/no/unknown | candidate/not tested/confirmed |  |

## 4. 文件流转图

```text
入口参数：
服务端解析：
文件名处理：
路径拼接：
权限判断：
存储位置：
后续访问方式：
预览 / 下载 / 解析 / 转换 / 删除链路：
```

## 5. 高风险候选点列表

| id | risk type | endpoint/source | reason | required dynamic proof | current status | next action |
|---|---|---|---|---|---|---|
|  | upload-bypass/file-read/file-write/path-boundary/object-key/archive/authorization |  |  | request + response + marker + fs before/after + controls | candidate/not tested |  |

## 6. 动态验证计划

| test id | endpoint | method | auth role | tenant | user | parameter | file operation | marker target | expected safe result | required evidence |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  | upload/read/write/preview/convert/extract | allowed/blocked/upload marker |  | request/response/marker/fs/log/control |

## 7. 已执行验证结果

| endpoint | method | auth role | tenant | user | parameter | file operation | marker target | expected safe result | actual result | evidence | severity | status | next action |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  | request/response/marker/fs/log/control | critical/high/medium/low/info | confirmed/candidate/false positive/blocked/not tested |  |

## 8. confirmed 漏洞

### FBV-YYYYMMDD-NNN

```yaml
id: FBV-YYYYMMDD-NNN
status: confirmed
vulnerability_type: ""
endpoint: ""
auth_role: ""
tenant: ""
request_sample: ""
response_summary: ""
marker_proof: ""
filesystem_before: ""
filesystem_after: ""
log_evidence: ""
positive_test: ""
negative_test: ""
blocked_test: ""
impact_scope: ""
not_false_positive_reason: ""
not_static_guess_reason: ""
minimal_fix: ""
regression_test: ""
rollback_status: "complete | incomplete | not required"
```

## 9. candidate 漏洞

| id | type | endpoint/source | candidate reason | missing evidence | downgrade reason | next proof needed |
|---|---|---|---|---|---|---|
|  |  |  |  | request/response/marker/fs/control/role/tenant |  |  |

## 10. false positive

| id | original suspicion | tested endpoint | evidence | expected security behavior | why not vulnerability |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 11. 未覆盖原因

| area | item | reason not covered | risk if untested | next action |
|---|---|---|---|---|
| upload/read/path/auth/tenant/dependency/worker/object-storage |  | no credential/service unavailable/no endpoint/tool unavailable/not applicable |  |  |

## 12. 下一轮必须补测的偏门路径

- [ ] avatar / logo / icon / image / media / attachment。
- [ ] import / export / backup / restore。
- [ ] preview / thumbnail / render / convert。
- [ ] template / theme / plugin / extension。
- [ ] report / invoice / pdf / document。
- [ ] locale / lang / i18n。
- [ ] log / debug / trace。
- [ ] admin-only 文件管理功能。
- [ ] 富文本编辑器上传接口。
- [ ] Markdown / HTML / PDF 渲染中的资源读取。
- [ ] GraphQL mutation / query 中的 file、path、key 字段。
- [ ] WebSocket / RPC 中的文件读取或上传消息。
- [ ] 老版本 API、隐藏 API、废弃路由。
- [ ] 测试接口、开发接口、debug 接口。
- [ ] 对象存储代理下载接口。
- [ ] CDN / static proxy / media proxy。
- [ ] 根据 URL 生成预览的功能。
- [ ] 导入压缩包后自动解压的功能。
- [ ] 用户自定义模板、主题、插件上传。
- [ ] 后台配置中可修改存储路径的功能。

## 13. 修复建议

| vulnerability id | affected component | minimal fix | server-side validation | authorization fix | regression test |
|---|---|---|---|---|---|
|  |  |  | canonical path check / extension+content validation / storage key isolation | owner+tenant+role check |  |

## 14. 回归测试用例

| test id | target | setup | request | expected result | evidence to collect |
|---|---|---|---|---|---|
|  |  | marker root + role context |  | blocked / allowed only within marker | request + response + marker + fs |

## 15. 反向审判降级结果

| id | original status | reviewed status | missing proof | decision | required retest |
|---|---|---|---|---|---|
|  | confirmed/candidate/false positive | confirmed/candidate/false positive/blocked/not tested |  | keep/downgrade/retest |  |

## 16. evidence manifest 索引

| id | evidence file/path | request | response | marker proof | filesystem state | logs | rollback |
|---|---|---|---|---|---|---|---|
|  |  | present/missing | present/missing | present/missing | present/missing | present/not available/missing | complete/incomplete/not required |
