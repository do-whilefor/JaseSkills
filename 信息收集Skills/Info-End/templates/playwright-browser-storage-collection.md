# Playwright / MCP 浏览器存储采集模板

本模板用于在授权本机项目中，通过 Playwright 或 Claude Playwright MCP 采集浏览器侧信息暴露证据，专门覆盖 cookie、localStorage、sessionStorage、IndexedDB、Cache Storage 与 service worker 相关缓存。

## 适用场景

- 需要验证信息是否暴露在浏览器本地存储中。
- 需要比较登录前、登录后、低权限、管理员、登出后、成员移除后、邀请过期后的浏览器状态差异。
- 需要确认前端缓存、Cache Storage、service worker 是否保存接口响应、配置、用户信息、token、文件 URL、预加载资源清单。
- 需要把浏览器证据交给 04 动态验证和 07 质量门禁。

## 禁止场景

- 不使用未授权账号。
- 不绕过登录、不伪造身份、不盗用 session。
- 不导出完整 cookie、token、私钥、密码、隐私数据。
- 不访问第三方真实业务系统。
- 不把浏览器存储中出现的关键词直接写成确定信息暴露，必须说明运行态来源、认证状态、角色要求和影响。

## 输入材料

- Base URL。
- 授权账号或已授权浏览器上下文。没有账号时只采集未认证视角。
- 需要访问的页面路径或业务流程。
- 角色标签，例如 unauthenticated、user、readonly、admin、removed-member、expired-invite。
- 禁止范围。

## MCP 执行步骤

使用 Claude Playwright MCP 或等价浏览器工具时，按以下最小路径执行：

1. 打开 Base URL，不访问外部非授权域名。
2. 记录当前角色、页面 URL、认证状态。
3. 访问目标页面或业务流程，只执行只读动作。
4. 读取并摘要 cookie：仅记录 name、domain、path、httpOnly、secure、sameSite、expires、value 长度、value hash、脱敏样本。
5. 读取 localStorage：记录 key、value 类型、长度、hash、脱敏样本、是否疑似敏感。
6. 读取 sessionStorage：记录 key、value 类型、长度、hash、脱敏样本、是否疑似敏感。
7. 读取 IndexedDB：记录数据库名、object store 名、记录数量、少量 key 名称或脱敏样本；默认不要导出完整 value。
8. 读取 Cache Storage：记录 cache 名、缓存请求 URL、method、资源类型、响应大小摘要；默认不要导出完整响应体。
9. 读取 service worker 注册信息：scope、scriptURL、状态、是否控制当前页面。
10. 登出或清 Cookie 后复测同一路径，比较存储是否残留敏感数据。
11. 将结果写入“浏览器存储暴露表”，再交给 04 做运行态复现，交给 07 做质量门禁。

## 可选脚本路径

基于文档延伸：如果本机有 Node.js 与 Playwright，可使用：

```bash
node scripts/browser-storage-collect-playwright.mjs \
  --url http://127.0.0.1:3000 \
  --out browser-storage.json \
  --label unauthenticated
```

非 localhost 但属于授权范围时，必须显式指定允许主机：

```bash
node scripts/browser-storage-collect-playwright.mjs \
  --url http://app.internal:8080 \
  --allow-host app.internal \
  --out browser-storage.json \
  --label user
```

如已有授权浏览器状态文件：

```bash
node scripts/browser-storage-collect-playwright.mjs \
  --url http://127.0.0.1:3000/dashboard \
  --state auth-state.json \
  --out browser-storage-user.json \
  --label user
```

## 输出格式

```md
# 浏览器存储采集结果

## 采集上下文
- Base URL：
- 页面 URL：
- 角色标签：
- 认证状态：
- 采集方式：Playwright MCP / Playwright Script / 手工浏览器
- 时间：

## Cookie 摘要
| 名称 | Domain | Path | HttpOnly | Secure | SameSite | 长度 | Hash | 脱敏样本 | 是否疑似敏感 | 证据编号 |
|---|---|---|---|---|---|---:|---|---|---|---|

## localStorage 摘要
| Key | 类型 | 长度 | Hash | 脱敏样本 | 上下文 | 是否疑似敏感 | 证据编号 |
|---|---|---:|---|---|---|---|---|

## sessionStorage 摘要
| Key | 类型 | 长度 | Hash | 脱敏样本 | 上下文 | 是否疑似敏感 | 证据编号 |
|---|---|---:|---|---|---|---|---|

## IndexedDB 摘要
| DB | Object Store | 记录数 | Key 样本 | Value 脱敏摘要 | 是否疑似敏感 | 证据编号 |
|---|---|---:|---|---|---|---|

## Cache Storage 摘要
| Cache | 请求 URL | Method | 资源类型 | 响应摘要 | 是否疑似敏感 | 证据编号 |
|---|---|---|---|---|---|---|

## Service Worker 摘要
| Scope | Script URL | 状态 | 是否控制页面 | 关联缓存 | 证据编号 |
|---|---|---|---|---|---|

## 角色/生命周期差异
| 状态 | 访问路径 | 存储变化 | 残留信息 | 结论 | 下一步动态验证 |
|---|---|---|---|---|---|
```

## 质量门槛

- 存储证据必须脱敏，不能输出完整值。
- IndexedDB 和 Cache Storage 默认只输出结构、数量、key 样本、URL、脱敏摘要。
- 浏览器存储命中只能作为候选；必须和运行态路径、角色要求、复现次数、影响判断关联。
- 如果浏览器工具不可用，必须标记“浏览器存储未覆盖”，不得编造结果。

##

该模板是基于原文“浏览器本地存储、cookie、sessionStorage、localStorage、IndexedDB 中暴露的信息”和“service worker 缓存、浏览器缓存”要求的工程化延伸，用于让 Claude 稳定执行采集和脱敏。
