# Basic Example

## 场景

本地授权项目运行在 `http://127.0.0.1:3000`。已知有附件上传接口和下载接口。只有普通用户 A 的测试登录态，没有租户环境。

## 输入

```yaml
project_root: "C:\\work\\demo-app"
local_base_url: "http://127.0.0.1:3000"
auth_contexts:
  user_a: "普通用户 A，本地测试 cookie 已提供"
tenant_contexts: []
test_marker_root: "C:\\work\\demo-app\\security-markers\\file-boundary-001"
evidence_output_dir: "C:\\work\\demo-app\\security-evidence\\file-boundary-001"
allowed_operations:
  - upload
  - download
  - read-marker
  - write-marker
rollback_policy: "测试结束后删除 marker 目录与测试上传记录"
```

## 执行路径

1. 创建 `allowed/allowed-read-marker.txt`、`blocked/blocked-read-marker.txt`、`upload/upload-write-marker.txt`。
2. 识别上传与下载路由。
3. 对上传接口执行 baseline、扩展名、MIME、文件名规范化、隐藏字段验证。
4. 对下载接口执行 allowed marker、blocked marker、不存在文件、id/path 冲突验证。
5. 因只有用户 A，不输出跨用户或跨租户 confirmed。
6. 所有缺少证据的结论进入 candidate 或 not tested。

## 合格 candidate 写法

```yaml
id: FBV-20260607-001
status: candidate
vulnerability_type: "file-read"
endpoint: "GET /api/files/download"
reason: "接口接受 path 参数并进入文件读取逻辑，但未完成 blocked marker 动态读取证明。"
missing_evidence:
  - blocked marker response body proof
  - filesystem before/after state
  - user B and tenant matrix
next_action: "使用 blocked marker 和不同身份重放请求；补齐响应与文件系统证据后再分级。"
```

## 禁止写法

```text
发现任意文件读取漏洞，风险严重。
```

该写法没有请求、响应、marker、文件系统状态、对照组、权限矩阵，不得作为 confirmed。
