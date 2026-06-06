# Top-Tier Authorized Pentest Skill Completion Contract v2

This contract closes the unfinished gaps found in the anti-lazy/browser rejudgement.
It does not claim that a target has been dynamically tested. It makes the Skill
package refuse unsupported conclusions until evidence exists.

## P0 Promotion Rules

A finding may be `confirmed` only when all of the following are true:

1. Scope is local/authorized and non-destructive.
2. Code evidence identifies exact file, line, route/component, source, guard and sink.
3. Real browser or equivalent HAR/API evidence exists.
4. Browser interaction coverage includes page open, scroll, interaction probing, runtime assets and artifacts.
5. Role/tenant matrix has been executed for authz, IDOR, tenant, admin or token claims.
6. Positive evidence and negative control are both attached.
7. Lazy JS ledger has no unresolved browser-trigger-required assets, or each has a documented not_applicable reason with evidence.
8. Variant expansion has been executed or each variant is ruled out with evidence.
9. Quality gate passes.
10. `_shared/quality/final_claim_guard.py --claim-level confirmed` allows the claim.

## Required Runtime Path

1. `project_inventory_extractor.py` inventories code, Markdown, configs and scripts.
2. `advanced_code_graph_extractor.py` extracts route/handler/source/sink candidates.
3. `lazy_js_asset_discovery.py` builds lazy JS/source-map/service-worker/API ledger.
4. `playwright_full_interaction_crawler.py` records real browser runtime evidence.
5. `browser_interaction_coverage_matrix.py` normalizes HAR/capture evidence.
6. `role_tenant_authz_matrix_builder.py` builds replay obligations for roles/tenants.
7. `vulnerability_candidate_engine.py` emits candidate-only findings.
8. `variant_expansion_engine.py` forces same-root/same-family expansion.
9. `quality_gate_v4_1.py` validates evidence manifests.
10. `final_claim_guard.py` blocks unsupported confirmed/dynamic-complete claims.

## Non-Execution Labels

Use only these labels when evidence is missing: `not_executed`, `partially_executed`,
`runtime_blocked`, `evidence_missing`, `needs_manual_review`, `candidate_only`.

## Forbidden Claims

The system must not write `full JS coverage`, `dynamic validation complete`,
`browser coverage complete`, or `confirmed vulnerability` unless the corresponding
machine gate allows it.
