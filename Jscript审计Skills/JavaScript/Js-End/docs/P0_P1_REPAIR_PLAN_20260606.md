# P0/P1 Repair Plan 2026-06-06

Implemented files for P0/P1 hardening:

- Runtime evidence: `js_playwright_safe_replay_executor.py`, `js_runtime_evidence_manifest.py`, `js_graphql_ws_runtime_replay.py`.
- Role/tenant gate: `js_role_tenant_diff.py` remains strict and requires authorization evidence.
- Backend acceptance: `js_backend_acceptance_probe.py` remains non-destructive and local/allowlisted by default.
- AST/wrapper: `js_wrapper_resolver.py` plus Babel/TypeScript backends.
- P1 parsers: sourcemap reconstruction, CDN history candidate enumeration, service worker cache audit, framework build artifact parser, schema alignment, hidden feature extraction, business-flow templates.
- OSS replay gate: `js_oss_replay_registry.py` creates import manifests but refuses to count registry-only samples as real replay.
- Dashboard: `js_evidence_dashboard_drilldown.py` links findings to evidence status.
- Install/env: `package.json`, `requirements.txt`, `installers/install.sh`, `installers/install.ps1`, and `install_and_env_check.py`.

Strict downgrade remains: without runtime evidence, role/tenant replay, backend acceptance, and real OSS samples, decision stays `not-top-tier`.
