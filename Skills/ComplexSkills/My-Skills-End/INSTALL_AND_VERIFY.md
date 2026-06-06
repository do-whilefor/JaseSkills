# Install and Verify — My-Skills-End 3.1-clean

Install this directory as one Claude Skill package. Do not split the internal `skills/` modules into separate external skills.

## Install

PowerShell:

```powershell
Copy-Item -Recurse .\My-Skills-End $env:USERPROFILE\.claude\skills\My-Skills-End -Force
```

Bash:

```bash
mkdir -p ~/.claude/skills
cp -R ./My-Skills-End ~/.claude/skills/My-Skills-End
```

## Verify from package root

```bash
python3 tools/runtime_check.py --out _audit_outputs/runtime_readiness.json
python3 tools/selftest.py --out _audit_outputs/selftest_result.json
python3 _shared/tests/smoke/anti_lazy_browser_gate_smoke_test.py
python3 _shared/tests/smoke/top_tier_completion_gate_smoke_test.py
python3 _shared/tests/adversarial/top_tier_adversarial_harness.py
python3 _shared/tests/e2e_replay/e2e_replay_runner.py
python3 _shared/tests/high_risk_replay/high_risk_replay_runner.py
python3 _shared/tests/oss_replay/oss_replay_runner.py
```

## Real target dynamic validation command shape

```bash
python3 skills/06-dynamic-browser-burp-mcp/scripts/playwright_full_interaction_crawler.py \
  --url http://localhost:3000 \
  --execute-clicks \
  --role member \
  --tenant tenant_a \
  --out _shared/runs/full_browser_interaction_capture.json
```

If Playwright browser runtime is missing, output must remain `runtime_unavailable` and no dynamic-validation claim may be promoted.

## Confirmed finding gate

```bash
python3 _shared/quality/final_claim_guard.py \
  --claim-level confirmed \
  --manifest _shared/runs/evidence_manifest.json \
  --browser-coverage _shared/runs/browser_interaction_coverage.json \
  --lazy-js-ledger _shared/runs/lazy_js_asset_ledger.json \
  --role-tenant-matrix _shared/runs/role_tenant_authz_matrix.json \
  --variant-expansion _shared/runs/variant_expansion.json
```
