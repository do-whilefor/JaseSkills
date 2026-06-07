# Basic Example：单一路由 SSRF canary 验证

## 输入

```text
project_root: C:\lab\demo-app
app_start_command: npm run dev
app_base_url: http://127.0.0.1:3000
canary_base_url: http://127.0.0.1:7777
evidence_dir: evidence/ssrf/
authorization_scope: 仅当前本地授权项目、本机 canary、测试容器网络。
prohibited_targets: 真实公网敏感地址、云 metadata、真实内网资产、公司内网、第三方服务、生产服务。
```

## 候选点

| 编号 | 路由/入口/功能 | 用户可控参数 | 参数来源 | 代码文件 | sink | 当前状态 |
|---|---|---|---|---|---|---|
| 1 | `/api/link-preview` 链接预览 | `url` | JSON body | `src/routes/linkPreview.ts` | `fetch` | candidate |

## case-id 与 marker

```text
case-id: SSRF-20260607-001-link-preview-url
marker: /ssrf-marker/link-preview/url/SSRF-20260607-001-link-preview-url
canary URL: http://127.0.0.1:7777/ssrf-marker/link-preview/url/SSRF-20260607-001-link-preview-url
```

## 正例验证

```http
POST /api/link-preview HTTP/1.1
Host: 127.0.0.1:3000
Content-Type: application/json

{"url":"http://127.0.0.1:7777/ssrf-marker/link-preview/url/SSRF-20260607-001-link-preview-url"}
```

保存：

```text
evidence/ssrf/SSRF-20260607-001-link-preview-url/request.http
evidence/ssrf/SSRF-20260607-001-link-preview-url/response.txt
evidence/ssrf/SSRF-20260607-001-link-preview-url/canary.log
evidence/ssrf/SSRF-20260607-001-link-preview-url/app.log
evidence/ssrf/SSRF-20260607-001-link-preview-url/code-chain.md
```

## 反例

浏览器或 curl 直接访问 canary：

```text
http://127.0.0.1:7777/ssrf-marker/link-preview/url/SSRF-20260607-001-link-preview-url-baseline
```

该请求只用于记录 baseline，不得计为 SSRF。

## blocked case

使用本地受控的非法 scheme 或本地受控阻断目标，验证服务端是否拒绝。不得访问真实 metadata、真实内网或第三方服务。

```http
POST /api/link-preview HTTP/1.1
Host: 127.0.0.1:3000
Content-Type: application/json

{"url":"file:///local-controlled-blocked-marker"}
```

## 结论规则

| 观察结果 | 状态 |
|---|---|
| canary 收到 marker，应用日志同 case-id，代码链到服务端 fetch，排除浏览器/工具误判 | confirmed |
| 应用保存参数但 canary 未回连 | candidate 或 needs_review |
| 前端直接请求 canary，服务端无日志 | needs_review，不得 confirmed |
| 非法 scheme 被拒绝且 canary 无回连 | blocked |
| 缺少反例或 blocked case | 降级，不得 confirmed |
