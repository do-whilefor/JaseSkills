# Install and verify

This directory is one installable Skill package. Keep `SKILL.md`, `_shared/`, `skills/`, `schemas/`, `tools/`, `tests/`, and `dashboard/` together.

## Windows PowerShell install

Run from the extracted `My-Skills-End` directory:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\INSTALL_TO_CLAUDE_SKILLS.ps1 -SkillName My-Skills-End -RunSelfTest
```

The script copies the whole package into your Claude skills directory and backs up an existing target directory before replacing it. If the script is already running from the target directory, it does not copy the directory into itself.

## Bash-compatible install

```bash
./INSTALL_TO_CLAUDE_SKILLS.sh My-Skills-End
```

## Local verification

Use the Python executable available on your workstation. On Windows, `py -3` and `python` are both supported; examples below use `python`.

```powershell
python tools/runtime_check.py --out _audit_outputs/runtime_readiness.json
python tools/selftest.py --out _audit_outputs/selftest_result.json
python _shared/tests/smoke/anti_lazy_browser_gate_smoke_test.py
python _shared/tests/smoke/top_tier_completion_gate_smoke_test.py
python _shared/tests/adversarial/top_tier_adversarial_harness.py
```

## Optional local dynamic capture

Only use local or explicitly authorized targets. Browser-backed claims require a successful Playwright browser launch and target-specific artifacts.

```powershell
python skills/06-dynamic-browser-burp-mcp/scripts/playwright_full_interaction_crawler.py `
  --url http://127.0.0.1:8000 `
  --out _audit_outputs/full_browser_interaction_capture.json
```

## Final claim guard

Run the final claim guard before reporting a confirmed finding:

```powershell
python _shared/quality/final_claim_guard.py `
  --claim-level confirmed `
  --manifest _audit_outputs/evidence_manifest.json `
  --browser-coverage _audit_outputs/browser_interaction_coverage.json `
  --lazy-js-ledger _audit_outputs/lazy_js_asset_ledger.json `
  --role-tenant-matrix _audit_outputs/role_tenant_authz_matrix.json `
  --variant-expansion _audit_outputs/variant_expansion.json
```
