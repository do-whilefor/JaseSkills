# My-Skills-End

This directory is a single installable Skill package for local, authorized security audit workflows. `SKILL.md` is the root entry. `skills/` contains routed internal modules. `_shared/` contains the knowledge base, vulnerability templates, schemas, evidence contracts, quality gates, replay fixtures and dashboard support.

## Preservation policy

- Keep `_shared/knowledge/` intact. Knowledge entries are hypothesis sources only; they are not direct vulnerability evidence.
- Keep `_shared/vulnerability_templates/` intact. These are the canonical vulnerability templates and report/evidence requirements.
- Keep executable overlays outside the canonical template tree in `_shared/executable_template_overlays/`.

## Authorized-use boundary

Use only on local projects, local labs, local fixtures, or targets where explicit authorization exists. Do not use this package for unauthorized scanning, exploitation, destructive testing, persistence, data theft, denial-of-service, credential abuse or stealth activity.

## Install on Windows

Run from the extracted package root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.\INSTALL_TO_CLAUDE_SKILLS.ps1 -SkillName My-Skills-End -RunSelfTest
```

## Install on Bash-compatible shells

```bash
./INSTALL_TO_CLAUDE_SKILLS.sh My-Skills-End
```

## Verify package health

Run from the package root. On Windows, use `py -3` or `python`; examples below use `python`.

```powershell
python tools/runtime_check.py --out _audit_outputs/runtime_readiness.json
python tools/selftest.py --out _audit_outputs/selftest_result.json
python _shared/tests/smoke/anti_lazy_browser_gate_smoke_test.py
python _shared/tests/smoke/top_tier_completion_gate_smoke_test.py
python _shared/tests/adversarial/top_tier_adversarial_harness.py
```

## Claim rule

A finding remains `candidate`, `likely`, `needs_manual_review`, or `runtime_blocked` until target-specific evidence exists. `confirmed` requires validated evidence manifest entries, code evidence, runtime evidence where applicable, role/tenant context, positive and negative controls, variant coverage and a passing quality gate.

## Key files

- `SKILL.md`
- `CLAUDE.md`
- `_shared/knowledge/`
- `_shared/vulnerability_templates/`
- `_shared/executable_template_overlays/executable_templates_index.json`
- `_shared/quality/final_claim_guard.py`
- `skills/03-code-knowledge-graph/scripts/semantic_graph_builder.py`
- `skills/07-vulnerability-hunting-engine/scripts/candidate_to_replay_plan.py`
- `dashboard/index.html`

## One-command local pipeline

```powershell
python tools/authorized_audit_pipeline.py C:\path	o\local-authorized-project --out-dir _audit_outputs/pipeline
```

The pipeline produces inventory, security graph, JS audit, attack surface, canonical candidates, extended candidates and replay plans. It intentionally blocks confirmed claims until executed evidence and quality gates exist.
