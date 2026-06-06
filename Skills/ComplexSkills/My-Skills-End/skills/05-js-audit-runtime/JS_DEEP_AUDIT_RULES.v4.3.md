# JS deep audit rules v4.3

Required outputs for promoted JS audit:

1. sourcemap original span mapping: generated file, source file, generated line, original line, sourcesContent hash.
2. chunk dependency graph: static import, dynamic import, preload, prefetch, service-worker cache edge.
3. API wrapper/interceptor dataflow: axios instance baseURL, request/response interceptor, fetch wrapper and header mutation.
4. GraphQL operation dataflow: operation name, fragment, persisted query hash, endpoint and guard mapping.
5. Electron/extension boundary dataflow: preload, contextBridge, IPC channel, content script, background script.
6. Every JS candidate must link to evidence manifest fields and quality gate obligations.

JS output cannot confirm vulnerabilities. It can only create candidate/evidence links.
