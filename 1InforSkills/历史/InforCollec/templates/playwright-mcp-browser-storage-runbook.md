# Playwright MCP 浏览器存储采集操作手册

用途：把浏览器态信息暴露采集写成 Claude 可执行的 MCP 操作流程，覆盖 cookie、localStorage、sessionStorage、IndexedDB、Cache Storage、Service Worker。该手册是“基于文档延伸”，用于落实原文档对浏览器本地存储、浏览器访问与 curl 访问差异、动态证据、脱敏输出的要求。

## 必须调用

- 用户要求检查浏览器本地存储、前端配置、token/cookie/session 暴露。
- 需要比较未登录、低权限、管理员、登出后旧 session 的浏览器态差异。
- 需要检查 PWA、Service Worker、Cache Storage、IndexedDB。
- 需要把浏览器截图、页面状态、存储摘要写入 evidence manifest。

## 禁止调用

- 未确认 Base URL 属于本机或授权服务。
- 用户要求输出完整 token、cookie、隐私数据。
- 用户要求用浏览器中的真实 token 调外部 API。
- 页面交互会修改、删除、污染业务数据。

## MCP 操作级流程

如果 Playwright MCP 可用，按等价工具能力执行；工具名称可能因环境不同而不同，不得编造不存在工具的执行结果。

### 0. 前置确认

1. 确认 Base URL、角色标签、授权范围。
2. 打开隔离浏览器上下文。不要复用用户日常浏览器 profile。
3. 记录 `role_label`：unauthenticated / low_privilege / admin / logged_out / removed_member / custom。

### 1. 导航与页面证据

使用 MCP 浏览器导航到 Base URL：

```text
browser.navigate(url=BaseURL)
browser.snapshot()
browser.take_screenshot(filename="EV-browser-page.png")
```

如果 MCP 工具名不同，使用等价“导航、快照、截图”能力。若不可用，标记为“浏览器 MCP 不可用，降级为脚本或手工步骤”，不得写成已执行。

### 2. 非 HttpOnly cookie 摘要

通过页面上下文采集 `document.cookie`。注意：HttpOnly cookie 无法通过 JS 读取；如果 MCP/browser context 没有 cookie API，只能说明“不覆盖 HttpOnly cookie 值”。

```javascript
(() => {
  const enc = new TextEncoder();
  async function sha256(s) {
    const b = await crypto.subtle.digest('SHA-256', enc.encode(String(s)));
    return Array.from(new Uint8Array(b)).map(x => x.toString(16).padStart(2, '0')).join('');
  }
  return Promise.all(document.cookie.split(';').filter(Boolean).map(async item => {
    const [name, ...rest] = item.trim().split('=');
    const value = rest.join('=');
    return {name, length: value.length, sha256: await sha256(value), sample: value.slice(0,4) + '****' + value.slice(-4)};
  }));
})()
```

### 3. localStorage / sessionStorage 摘要

```javascript
(async () => {
  const enc = new TextEncoder();
  async function sha256(s) {
    const b = await crypto.subtle.digest('SHA-256', enc.encode(String(s)));
    return Array.from(new Uint8Array(b)).map(x => x.toString(16).padStart(2, '0')).join('');
  }
  async function dumpStorage(store) {
    const out = [];
    for (let i=0; i<store.length; i++) {
      const key = store.key(i);
      const value = store.getItem(key) || '';
      out.push({key, length: value.length, sha256: await sha256(value), sample: value.slice(0,4) + '****' + value.slice(-4)});
    }
    return out;
  }
  return {localStorage: await dumpStorage(localStorage), sessionStorage: await dumpStorage(sessionStorage)};
})()
```

### 4. IndexedDB 摘要

```javascript
(async () => {
  if (!indexedDB.databases) return {supported:false, reason:'indexedDB.databases unavailable'};
  const dbs = await indexedDB.databases();
  return {supported:true, databases: dbs.map(d => ({name:d.name || null, version:d.version || null}))};
})()
```

只记录数据库名、版本、对象仓库名；除非用户明确授权且数据属于测试环境，不读取完整记录值。读取记录时仍只输出字段名、类型、长度、hash。

### 5. Cache Storage / Service Worker 摘要

```javascript
(async () => {
  const cacheNames = ('caches' in window) ? await caches.keys() : [];
  const cacheSummary = [];
  for (const name of cacheNames) {
    const c = await caches.open(name);
    const reqs = await c.keys();
    cacheSummary.push({
      cacheName: name,
      requestCount: reqs.length,
      requests: reqs.slice(0,50).map(r => {
        const u = new URL(r.url);
        return {origin: u.origin, path: u.pathname, queryKeys: Array.from(u.searchParams.keys()).sort()};
      })
    });
  }
  const regs = ('serviceWorker' in navigator) ? await navigator.serviceWorker.getRegistrations() : [];
  return {cacheSummary, serviceWorkers: regs.map(r => ({scope:r.scope, active: !!r.active, scriptURL: r.active ? r.active.scriptURL : null}))};
})()
```

URL 中不得输出完整 query value。只输出 host/origin、path、query keys、hash。

## 输出格式

输出到 `templates/finding-detail.md` 或 evidence manifest：

| 字段 | 内容 |
|---|---|
| role_label | 角色标签 |
| url | Base URL |
| cookies_summary | 非 HttpOnly cookie 摘要 |
| local_storage_summary | key/length/hash/sample |
| session_storage_summary | key/length/hash/sample |
| indexeddb_summary | db/store/field/type 摘要 |
| cache_storage_summary | cache 名、请求数量、路径摘要 |
| service_worker_summary | scope、scriptURL 摘要 |
| screenshot_evidence | 截图证据编号 |
| limitations | HttpOnly 不可读、MCP 不可用、权限不足等 |
| why_reportable_or_not | 能/不能报告原因 |

## 回流规则

- 采集结果只证明“浏览器态存在”，不自动证明漏洞。
- 任何 token/cookie/隐私数据必须脱敏。
- 需要 04 动态验证确认运行态可访问性。
- 需要 07 质量门禁判定是否可报告。
