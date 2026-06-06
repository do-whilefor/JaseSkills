# Info-End Engineering System Audit Notes

## Preservation decision

Existing `knowledge/`, `templates/`, `detectors/`, `rules/`, `examples/`, and vulnerability/finding templates are preserved. Cleanup must mark stale, conflicting, or rejected material in indexes or human review queues instead of deleting original knowledge or templates.

## Real package structure after repair

- `SKILL.md`, `README.md`, `CAPABILITY_INDEX.md`: top-level Skill entry, usage, capability index.
- `00-master-info-exposure-orchestrator/` through `08-skill-adversarial-audit-regression/`: existing phase Skills.
- `scripts/`: legacy and promoted executable helpers, including scope, project fingerprint, route/API, JS, hidden info, manifest, quality gate, report and runtime helpers.
- `collectors/`: newly separated executable collectors for route, JS asset, config, dependency, docs, CI/CD, IaC, GraphQL, WebSocket, sourcemap and hidden parameter collection.
- `analyzers/`: newly separated manifest analyzers for fingerprint, endpoint/parameter, auth, role/tenant, frontend/backend correlation, secret redaction and evidence quality.
- `quality/`: newly separated gates for scope, secret redaction, evidence completeness, anti-hallucination and coverage.
- `schemas/`: existing schemas plus `information-finding.schema.json`, `endpoint.schema.json`, `parameter.schema.json`, and `collection-run.schema.json`.
- `reports/`: newly separated Markdown, JSON, CSV and evidence manifest summary report generators.
- `templates/`: existing report, evidence, quality, validation and vulnerability/finding templates; preserved.
- `knowledge/`: existing knowledge root; preserved.
- `tests/fixtures/engineering_system/`: added positive fixture covering hidden endpoint, hidden parameter, sourcemap, GraphQL, WebSocket, secret redaction, multi-role/tenant signals, CI/CD and IaC.
- `tests/test_engineering_system.py`: added regression tests for the new engineering system.
- `info_end_run.py`: one-command pipeline for collectors -> manifest -> analyzers -> quality gates -> reports.

## Collector matrix

| Collector | Input | Output | Evidence focus | Boundary |
|---|---|---|---|---|
| `collectors/route_collector.py` | authorized local project | JSON report | HTTP routes, OpenAPI/Postman paths, GraphQL/proto hints, literal API candidates | static, no network |
| `collectors/js_asset_collector.py` | authorized local JS/build assets | JSON report | chunks, dynamic import, service worker, manifest/HTML hidden paths, frontend URLs, flags | static; regex literals plus AST handoff limitation |
| `collectors/config_collector.py` | authorized local configs | JSON report | config files, env/config keys, secret-name signals, security config terms | values redacted |
| `collectors/dependency_collector.py` | package and lock files | JSON report | package managers, dependencies, scripts, postinstall/prepare, lock files | CVE/deprecation marked needs online verification |
| `collectors/docs_collector.py` | docs/tests text | JSON report | documented endpoints, TODO/deprecated/legacy/fixture/seed/error signals | docs may be stale |
| `collectors/ci_cd_collector.py` | CI/CD files | JSON report | actions, secrets usage, deploy/cache/artifact signals | no runner/cloud query |
| `collectors/iac_collector.py` | Docker/K8s/Terraform/Helm manifests | JSON report | base images, ports, env, secret refs, cloud resources | local manifests only |
| `collectors/graphql_collector.py` | GraphQL files and JS | JSON report | schema symbols, operations, introspection signals | static only |
| `collectors/websocket_collector.py` | source files | JSON report | WebSocket stack signals and event names | static only |
| `collectors/sourcemap_collector.py` | `.map` files | JSON report | original paths and hidden/deleted API candidates from `sourcesContent` | stale/dead-code risk |
| `collectors/hidden_parameter_collector.py` | source/docs/schema files | JSON report | query/body/path/header/cookie/tenant/role/debug/include/expand/etc. signals | static; needs binding correlation |

## Analyzer matrix

| Analyzer | Input | Output | Logic |
|---|---|---|---|
| `analyzers/project_fingerprint_analyzer.py` | evidence manifest | finding JSON | summarizes structure/language/framework/package evidence |
| `analyzers/endpoint_parameter_analyzer.py` | evidence manifest | finding JSON | counts and groups endpoint/parameter evidence requiring binding review |
| `analyzers/auth_surface_analyzer.py` | evidence manifest | finding JSON | finds auth/session/permission/role signals |
| `analyzers/role_tenant_surface_analyzer.py` | evidence manifest | finding JSON | finds tenant/org/workspace/account/project/role boundary identifiers |
| `analyzers/frontend_backend_correlation_analyzer.py` | evidence manifest | finding JSON | coarse frontend/backend route coexistence and correlation hints |
| `analyzers/secret_redaction_analyzer.py` | evidence manifest | finding JSON | checks redaction status and unredacted secret-like values |
| `analyzers/evidence_quality_analyzer.py` | evidence manifest | finding JSON | checks source/reason/limitation/confirmed-claim quality |

## Quality gates

- `quality/scope_gate.py`: fails on out-of-scope input/evidence paths.
- `quality/secret_redaction_gate.py`: fails on unredacted secret-like values in evidence.
- `quality/evidence_completeness_gate.py`: requires source file, line range, collector, timestamp, confidence, reason, raw hash, redacted evidence, reproduction command and limitation.
- `quality/anti_hallucination_gate.py`: blocks unsupported confirmed claims, unknown source files and CVE-like claims without online verification.
- `quality/coverage_gate.py`: reports analyzed surface counts and mandatory evidence sections.
- `quality/unified_quality_gate.py`: runs all gates.

## Status semantics

All static local findings default to `candidate`. Items become `needs_review` when static evidence is sensitive, ambiguous, auth/tenant-relevant, stale/dead-code-prone, or needs runtime/online verification. `confirmed` must not be used unless explicit runtime/manual validation evidence and reason are present. CVEs are never invented; dependency risk is `needs_online_verification` unless backed by separate verified data.

## One-command run

```bash
python info_end_run.py \
  --input /path/to/authorized/project \
  --scope /path/to/authorized/project \
  --output /tmp/info-end-out \
  --max-files 5000 \
  --scan-profile standard
```

Outputs include collector JSON, `evidence-manifest.json`, analyzer JSON, `unified-quality-gate.json`, `markdown_report.md`, `json_report.json`, `csv_summary.csv`, `evidence_manifest_report.json`, and `collection-run.json`.

## Verification commands

```bash
python info_end_run.py --input tests/fixtures/engineering_system --scope tests/fixtures/engineering_system --output /tmp/info-end-fixture --max-files 500
python scripts/evidence-schema-validate.py /tmp/info-end-fixture/evidence-manifest.json --kind evidence-manifest
python quality/secret_redaction_gate.py --input /tmp/info-end-fixture/evidence-manifest.json
python quality/anti_hallucination_gate.py --input /tmp/info-end-fixture/evidence-manifest.json
python quality/unified_quality_gate.py --input tests/fixtures/engineering_system --scope tests/fixtures/engineering_system --manifest /tmp/info-end-fixture/evidence-manifest.json
python -m pytest -q tests/test_engineering_system.py
```

## Known limitations

- JS wrapper/baseURL/callgraph correlation is still partial. `scripts/js-ast-endpoint-extractor.mjs` supports AST when `@babel/parser` is installed; the new Python collectors record static evidence and limitations but do not fully replace a JS callgraph engine.
- Python/Java/PHP/Ruby/Go/Rust/C# framework route extraction remains mixed: existing scripts improve coverage, but some collectors still use generic route patterns.
- Dependency CVE/deprecation/typosquatting checks are intentionally offline and marked needs online verification.
- Runtime reachability, role differential validation and tenant boundary proof require authorized dynamic replay, accounts and base URLs.
- Sourcemap and generated client evidence may represent stale/dead code.
