# 21 JS Runtime Evidence Orchestration

## Trigger
Use when a JS audit needs real browser replay, HAR, trace, screenshots, request/response evidence, GraphQL/WebSocket runtime replay, role/tenant mapping, or a redacted evidence manifest.

## Input
Authorized local/test URL, optional Playwright storageState files, role/tenant matrix, replay plan, HAR/Burp exports, screenshots, trace.zip, GraphQL/WebSocket scenarios.

## Execution
1. Generate a safe replay plan with `scripts/js_browser_lazyload_replay_plan.py`.
2. Generate a Playwright spec with `scripts/js_playwright_safe_replay_executor.py --generate-spec`.
3. Execute only against authorized targets with `--execute`; no delete, real payment, external callback, or bulk enumeration actions.
4. Import HAR/trace/screenshots with `scripts/js_runtime_evidence_bridge.py`.
5. Build `js_evidence_manifest.json` with `scripts/js_runtime_evidence_manifest.py`.
6. Run `scripts/js_graphql_ws_runtime_replay.py` only with safe local/allowlisted scenarios.

## Output
`js_playwright_execution.json`, `js_runtime_evidence.json`, `js_evidence_manifest.json`, `js_graphql_ws_runtime_replay.json`, screenshots, trace, HAR.

## Quality gate
Plan-only evidence is never ready. Runtime is ready only when HAR, trace, screenshots, request/response metadata, and role/tenant mapping are all present.
