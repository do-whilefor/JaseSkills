# JS 深度审计矩阵

所有 JS 结论必须进入 API → Method → URL → Headers → Body Params → Hidden Params → Auth Requirement → Role Requirement → Tenant Scope → Frontend Guard → Backend Candidate Handler → Vulnerability Candidate 图谱。

必须覆盖：HTML script、动态 chunk、Webpack/Vite/Rollup/Next/Nuxt/Angular/React/Vue、sourcemap、service worker、worker、WASM glue、Electron preload/IPC、浏览器扩展、GraphQL、REST、WebSocket、fetch/axios/graphql/apollo/urql/ky/superagent wrapper、baseURL、feature flag、隐藏参数、前端 guard、storage、postMessage、DOM sink。

升级规则：前端发现 endpoint、hidden param、guard bypass 只可标记 candidate；只有绑定后端 handler、权限/租户矩阵、HAR/请求响应和负向控制后才能 promoted。
