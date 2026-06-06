# Lazy JS Asset Discovery Matrix

This matrix is a hard execution contract for `05-js-audit-runtime`. It closes the lazy-loading failure mode where an audit reads only the homepage, README, or a few grep hits.

## Required static discovery scope

The extractor must inspect, when present, all of the following local project assets:

- `package.json` scripts and lockfiles.
- Vite, Webpack, Rollup, Babel, TypeScript, Next, Nuxt and Angular build configuration.
- `pages/`, `app/`, `routes/`, `router/`, `views/`, `components/`, `layouts/`, `middleware/`, `plugins/`, `src/`, `public/`, `dist/`, `build/`, `.next/`, `.nuxt/` and static asset directories.
- `import()`, `React.lazy`, `Suspense`, `next/dynamic`, Vue async components, Nuxt routes and Angular `loadChildren` lazy modules.
- build manifests, chunk manifests, precache manifests, `asset-manifest.json`, `manifest.json`, `preload`, `prefetch`, `modulepreload`, service workers and Workbox cache manifests.
- source maps and `sourcesContent` where present.
- API clients, wrappers, interceptors, base URLs, GraphQL operations, persisted queries, WebSocket, SSE, `postMessage`, feature flags, route guards, permission keys and hidden admin/internal/debug/test routes.

## Required runtime-triggered discovery scope

Static discovery is not sufficient. The dynamic module must attempt or explicitly mark unavailable browser-triggered collection for:

- login-before and login-after navigation;
- click, scroll, input, hover, dropdown expansion, tab switching, modal opening, pagination, search and form validation;
- deep route refresh, query/hash mutation, 403/404/500 pages;
- role and tenant switching;
- newly observed chunks, APIs, storage entries, cookies, WebSocket/SSE and GraphQL calls.

## Output fields

`lazy_js_asset_discovery.py` must emit a JSON ledger containing:

- `static_js_assets`
- `html_js_references`
- `build_manifests`
- `source_maps`
- `service_workers`
- `dynamic_imports`
- `framework_lazy_routes`
- `frontend_routes`
- `api_clients`
- `graphql`
- `websocket_sse`
- `feature_flags`
- `hidden_route_signals`
- `browser_trigger_required`
- `evidence_gaps`

## Promotion rule

A JS audit may only be called complete when the lazy ledger exists and the browser interaction coverage matrix either contains real browser evidence or explicitly states `runtime_missing`. `runtime_missing` blocks dynamic-validation claims and keeps findings at `candidate` or `needs_review`.
