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
