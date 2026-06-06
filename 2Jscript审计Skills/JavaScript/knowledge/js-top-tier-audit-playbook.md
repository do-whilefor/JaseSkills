# JS 顶级收集、分析、审计 Playbook

## 收集优先级

1. HTML script、modulepreload、asset-manifest、build-manifest、routes-manifest、app-build-manifest、vite manifest、precache manifest。
2. Webpack/Vite/Next/Nuxt/Angular/React lazy/SvelteKit chunk 与 runtime chunk。
3. Source Map：必须解析 `sources`、`sourcesContent`、原始路径、隐藏 endpoint、secret/config 线索。
4. Service Worker / Workbox / Cache Storage / stale asset replay。
5. Web Worker / SharedWorker / WASM glue。
6. GraphQL query/mutation/subscription、persisted query hash、WebSocket/SSE schema。
7. Electron preload、browser extension content/background、mobile WebView bridge。
8. 登录后、管理员、租户、feature flag、地区/语言差异 chunk。

## 审计规则

- Regex 只能作为候选发现，不得升级为语义审计。
- AST backend 必须能产出 imports/calls/memberWrites/string routes，并可映射 source/sink/auth/tenant。
- Source-sink 必须证明 source → transform → sink；否则写 candidate-only。
- 所有严重候选必须要求非破坏性动态验证与证据 manifest。

## 严重漏洞链

DOM XSS / postMessage / prototype pollution / hidden API / GraphQL hidden mutation / WebSocket authz / OAuth/JWT / Service Worker cache poisoning / CDN stale asset / Electron IPC / Extension messaging / WebView bridge / WASM boundary / supply chain。
