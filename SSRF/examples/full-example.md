# Full Example：本地授权项目 SSRF 动态验证与反向审判

## 1. 环境记录

| 输入项 | 示例值 |
|---|---|
| project_root | `C:\lab\demo-app` |
| app_start_command | `npm run dev` |
| app_base_url | `http://127.0.0.1:3000` |
| canary_base_url | `http://127.0.0.1:7777` |
| evidence_dir | `evidence/ssrf/` |
| authorization_scope | 仅当前本地授权项目、本机 canary、测试容器网络、测试目录 marker 服务 |
| prohibited_targets | 真实公网敏感地址、云 metadata、真实内网资产、公司内网、第三方服务、生产服务 |

## 2. 暴露面矩阵片段

| 编号 | 路由/入口/功能 | 用户可控参数 | 参数来源 | 代码文件 | 调用链 | sink | 是否服务端请求 | 是否跟随跳转 | 是否有协议限制 | 是否有 host/IP 限制 | 是否有 DNS 解析校验 | 是否存在解析差异风险 | 是否异步触发 | 是否需要登录 | 需要的角色 | 初始风险等级 | 动态验证计划 | 当前状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | link preview | `url` | JSON body | `src/routes/linkPreview.ts` | controller → previewService → fetch | fetch | unknown | unknown | unknown | unknown | unknown | yes | no | yes | 普通用户 | medium | canary marker 正例、浏览器反例、非法 scheme blocked | candidate |
| 2 | webhook 测试按钮 | `endpoint` | admin form | `src/jobs/webhookTest.ts` | controller → queue → worker → httpClient | axios | unknown | yes | unknown | unknown | unknown | yes | yes | yes | 管理员 | high | 观察队列日志、worker 日志、canary marker | candidate |
| 3 | PDF 预览 | HTML 中远程资源 | uploaded HTML | `src/pdf/render.ts` | upload → renderer → remote resource load | PDF renderer | unknown | unknown | unknown | unknown | unknown | yes | maybe | yes | 普通用户 | high | 本地 HTML 引用 canary marker，观察 renderer 请求 | candidate |

## 3. source → sink 数据流图

```text
普通用户 JSON body.url
  -> POST /api/link-preview
  -> LinkPreviewController.parse(body.url)
  -> PreviewService.fetchPreview(targetUrl)
  -> fetch(targetUrl)
  -> http://127.0.0.1:7777/ssrf-marker/link-preview/url/SSRF-20260607-001-link-preview-url
```

## 4. 动态验证记录

### Case 1：link preview

| 字段 | 内容 |
|---|---|
| case-id | SSRF-20260607-001-link-preview-url |
| marker | `/ssrf-marker/link-preview/url/SSRF-20260607-001-link-preview-url` |
| 触发请求 | `evidence/ssrf/SSRF-20260607-001-link-preview-url/request.http` |
| canary 日志 | `evidence/ssrf/SSRF-20260607-001-link-preview-url/canary.log` |
| 应用日志 | `evidence/ssrf/SSRF-20260607-001-link-preview-url/app.log` |
| 代码链 | `evidence/ssrf/SSRF-20260607-001-link-preview-url/code-chain.md` |
| 反例 | 浏览器直连 marker-baseline，标记为非 SSRF |
| blocked case | 本地受控非法 scheme 被拒绝 |
| 结论 | 仅当以上全部存在且来源可归因为目标应用服务端时 confirmed；否则降级 |

### Case 2：webhook 测试按钮

| 字段 | 内容 |
|---|---|
| case-id | SSRF-20260607-002-webhook-test-endpoint |
| marker | `/ssrf-marker/webhook-test/endpoint/SSRF-20260607-002-webhook-test-endpoint` |
| 必须证据 | 请求样本、应用日志、任务 id、队列日志、worker 日志、canary 日志、代码链 |
| 特殊判定 | 只有保存 webhook endpoint 不算 confirmed；必须证明 worker 实际请求 canary |
| 结论 | 缺 worker 日志或 canary 回连则 candidate/needs_review |

### Case 3：PDF 预览

| 字段 | 内容 |
|---|---|
| case-id | SSRF-20260607-003-pdf-preview-resource |
| marker | `/ssrf-marker/pdf-preview/resource/SSRF-20260607-003-pdf-preview-resource` |
| 本地文件内容 | HTML 中只引用本地 canary marker，不引用外部服务 |
| 必须证据 | 上传请求、预览请求、renderer 日志、canary 日志、代码链、反例、blocked case |
| 结论 | renderer 未请求 canary 不得 confirmed |

## 5. 反向审判片段

| case-id | 原状态 | 审判问题 | 证据 | 修复后状态 |
|---|---|---|---|---|
| SSRF-20260607-001-link-preview-url | confirmed | 缺 blocked case | 未找到 `blocked.md` | candidate |
| SSRF-20260607-002-webhook-test-endpoint | candidate | 缺 worker 日志 | 只有保存 endpoint 记录 | needs_review |
| SSRF-20260607-003-pdf-preview-resource | confirmed | canary 请求 User-Agent 为浏览器 | `canary.log` 显示 Mozilla | needs_review |

## 6. 修复建议片段

| 问题 | 修复措施 | 回归测试 |
|---|---|---|
| link preview 直接接受完整 URL | 改为服务端白名单资源 id；只允许 http/https；解析后校验；连接前校验最终 IP；跳转后重新校验；禁止回环/链路本地/私有网段，除非走隔离代理 | 输入 canary、redirector、本地受控 blocked 目标，确认被拒绝或被安全代理处理 |
| webhook 测试按钮 | 域名白名单、签名、限速、审计；记录触发用户、租户、目标地址、最终地址；worker 执行前重复校验 | 低权限用户不得触发高权限 worker 请求；租户 A 不得影响租户 B |
| PDF/HTML 预览 | 默认禁用远程资源；必要时走隔离代理；渲染前后校验最终地址；记录资源加载日志 | HTML 中本地 canary marker 不应被 renderer 直接访问，或访问必须经隔离代理并可审计 |

## 7. 最终报告降级规则

- canary 无回连：candidate 或 needs_review。
- canary 回连但来源不能证明是目标服务端：needs_review。
- 浏览器、测试工具、redirector 自身请求 canary：误报排除。
- 缺应用日志、代码链、正例、反例、blocked case、复现步骤、回归测试任一项：不得 confirmed。
- high/critical 只允许用于 confirmed 且满足严重性条件的 case。
