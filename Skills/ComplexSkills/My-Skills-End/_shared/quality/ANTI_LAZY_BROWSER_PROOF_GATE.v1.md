# Anti-Lazy Browser Proof Gate v1

This gate prevents three classes of audit failure:

1. concluding from README/homepage-only inspection;
2. claiming JS coverage without lazy chunk/source map/service worker/router/API-client discovery;
3. claiming dynamic validation without browser interaction evidence.

## Hard blockers

A run is blocked from `confirmed` if any of these are true:

- no concrete file paths were scanned;
- no lazy JS asset ledger exists;
- the lazy ledger lacks checks for dynamic imports, source maps, service workers, build manifests and API clients;
- no browser interaction coverage matrix exists;
- the browser matrix says `runtime_missing`, but the report claims dynamic validation completed;
- no click, scroll, input or route interaction evidence exists while the report claims frontend coverage;
- no role/tenant matrix exists for authz, IDOR, tenant, GraphQL, WebSocket, OAuth, CORS or admin escalation findings;
- no negative control exists for a confirmed finding;
- candidate-only JS findings are written as confirmed vulnerabilities.

## Allowed downgrade

Tool absence may downgrade `browser_executed` to `runtime_missing`, but it must not downgrade evidence requirements. The final status must become `candidate`, `needs_review`, `validation_blocked` or `rejected`, not `confirmed`.

## Required outputs

- `lazy_js_asset_ledger.schema.json` compliant ledger.
- `browser_interaction_coverage.schema.json` compliant matrix.
- gate result with `passed`, `blocked_reasons`, `evidence_gaps` and `promotion_policy`.
