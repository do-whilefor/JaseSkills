# Security Audit Workflow

This workflow is local-only. It is for user-owned source code, local fixtures, local replay packages, and explicitly authorized lab targets. It must not be used for third-party probing, destructive writes, credential abuse, persistence, stealth, denial-of-service, or real data exfiltration.

## Execution stages

1. Authorization and scope gate: record local path, allowed hosts, allowed accounts, prohibited actions, and rollback assumptions before running any dynamic step.
2. Project intelligence: inventory languages, frameworks, dependency manifests, configuration files, routes, OpenAPI/GraphQL artifacts, seed data, mock accounts, and local startup instructions.
3. Code graph extraction: produce candidate Route → Handler → Middleware → AuthN → AuthZ → Parameter → Model → Sink → Evidence links. If a full parser runtime is missing, mark output as candidate-only.
4. JS asset extraction: identify local HTML/JS references, chunks, source maps, endpoints, GraphQL operations, WebSocket/SSE endpoints, storage use, postMessage, service workers, secret-like strings, and frontend authorization logic.
5. Attack-surface mapping: merge source, JS, config, and runtime observations into a single asset and route ledger.
6. Candidate generation: create vulnerability candidates with explicit source, sink, context, false-positive controls, and dynamic validation requirements. Candidates are not confirmed findings.
7. Dynamic validation: only non-destructive local validation is allowed. Valid statuses are STATIC_CANDIDATE, DYNAMIC_ATTEMPTED, DYNAMIC_CONFIRMED, DYNAMIC_BLOCKED, DYNAMIC_INCONCLUSIVE, NOT_TESTED, and UNSAFE_TO_TEST.
8. Evidence manifest: bind source file ranges, commands, request/response artifacts, HAR, screenshots, console logs, replay ids, and hashes to each candidate.
9. Quality gate: block confirmed findings unless required code evidence, dynamic evidence, scope boundary, impact path, negative control, and false-positive exclusion are present.
10. Reporting: reports must distinguish candidate, confirmed, inconclusive, blocked, and needs_review. Never convert a model guess or tool alert into a confirmed vulnerability.

## Promotion policy

A capability is IMPLEMENTED only when it has a file, executable code or executable procedure, schema/structured output, fixture, positive and negative test evidence, failure handling, quality gate, evidence chain, local run result, and report mapping. Missing one of these conditions requires PARTIAL, CLAIM_ONLY, BROKEN, UNKNOWN, or DANGEROUS_OR_UNSAFE.


## Anti-lazy JS and real browser proof gate

The user-requested lazy-loading and browser-interaction requirements are preserved in `_shared/requirements/USER_REQUESTED_LAZY_BROWSER_REQUIREMENTS.md`. For frontend or dynamic-validation tasks, route through these additional hard gates before final reporting:

1. `skills/05-js-audit-runtime/scripts/lazy_js_asset_discovery.py` must produce a lazy JS asset ledger for dynamic import, lazy routes, chunks, source maps, service workers, build manifests, API clients, GraphQL and WebSocket/SSE signals.
2. `skills/06-dynamic-browser-burp-mcp/scripts/browser_interaction_coverage_matrix.py` must produce a browser interaction matrix for click, scroll, input, hover, menu, tab, modal, search, pagination, deep-route, error-page, role and tenant coverage.
3. `_shared/quality/anti_lazy_browser_proof_gate.py` blocks any claim of complete JS coverage or dynamic validation when the ledger or matrix is missing.
4. If browser runtime is unavailable, output `runtime_missing`; do not claim browser validation completed.
5. Candidate JS or browser evidence still requires evidence manifest validation, negative control and quality gate before `confirmed`.

Operational commands:

```powershell
python skills/05-js-audit-runtime/scripts/lazy_js_asset_discovery.py C:\path\to\local-project --out _shared/runs/lazy_js_asset_ledger.json
python skills/06-dynamic-browser-burp-mcp/scripts/browser_interaction_coverage_matrix.py --capture-json _shared/runs/playwright_local_capture_result.json --out _shared/runs/browser_interaction_coverage.json
python _shared/quality/anti_lazy_browser_proof_gate.py --lazy-ledger _shared/runs/lazy_js_asset_ledger.json --browser-matrix _shared/runs/browser_interaction_coverage.json
```
