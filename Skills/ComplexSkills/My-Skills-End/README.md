# My-Skills-End — top-tier authorized pentest skills (3.1-clean)

This directory is a single installable Claude Skill package. `SKILL.md` is the root entry; `skills/` contains internal routed modules; `_shared/` contains knowledge, templates, schemas, evidence contracts, quality gates, replay fixtures and release metadata.

## Preservation policy

- Original knowledge base: `_shared/knowledge/` is preserved.
- Original vulnerability templates: `_shared/vulnerability_templates/` is preserved as the canonical template tree.
- Executable template overlays are stored separately in `_shared/executable_template_overlays/` to avoid polluting or overwriting the original templates.

## Authorized-use boundary

Use only on local projects, local labs, local fixtures, or targets where you have explicit authorization. Do not use this package for unauthorized scanning, exploitation, destructive testing, persistence, data theft, denial-of-service, credential abuse or stealth activity.

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

## Verify package health

Run from `My-Skills-End/`:

```bash
python3 tools/runtime_check.py --out _audit_outputs/runtime_readiness.json
python3 tools/selftest.py --out _audit_outputs/selftest_result.json
python3 _shared/tests/smoke/anti_lazy_browser_gate_smoke_test.py
python3 _shared/tests/smoke/top_tier_completion_gate_smoke_test.py
python3 _shared/tests/adversarial/top_tier_adversarial_harness.py
```

## Claim rule

A finding remains `candidate`, `likely`, `needs_manual_review`, or `runtime_blocked` until all required target-specific evidence exists. `confirmed` requires evidence manifest, browser/HAR/screenshot/DOM/console/storage evidence, lazy JS ledger, role/tenant matrix, positive and negative replay, variant expansion, and final quality gate.

## Key files

- `SKILL.md`
- `CLAUDE.md`
- `VERSION.md`
- `CHANGELOG.md`
- `PACKAGE_CLEANUP_REPORT.md`
- `_shared/release/VERSION.json`
- `_shared/executable_template_overlays/executable_templates_index.json`
- `_shared/quality/final_claim_guard.py`
- `skills/03-code-knowledge-graph/scripts/semantic_graph_builder.py`
- `skills/07-vulnerability-hunting-engine/scripts/candidate_to_replay_plan.py`
- `dashboard/index.html`
