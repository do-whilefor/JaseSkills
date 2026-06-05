# Install and Verify

Copy the `authorized_security_audit_system` directory into the Claude Skills directory as one installable skill. The `skills/` subdirectories are internal routed modules.

PowerShell:

```powershell
Copy-Item -Recurse .\authorized_security_audit_system $env:USERPROFILE\.claude\skills\authorized_security_audit_system -Force
```

Bash:

```bash
mkdir -p ~/.claude/skills
cp -R authorized_security_audit_system ~/.claude/skills/authorized_security_audit_system
```

Verify from the package root:

```bash
python3 tools/runtime_check.py --out _audit_outputs/runtime_readiness.json
python3 tools/selftest.py --out _audit_outputs/selftest_result.json
python3 _shared/tests/adversarial_test_harness.py
python3 _shared/tests/e2e_replay/e2e_replay_runner.py
python3 _shared/tests/high_risk_replay/high_risk_replay_runner.py
python3 _shared/tests/oss_replay/oss_replay_runner.py
```

`playwright_browser_runtime_ready=false` blocks browser dynamic-ready claims. OSS replay adapters with `manual_required_missing_local_checkout` are not promoted evidence. Regex/AST-lite outputs are candidate-only unless parser readiness explicitly says runtime_ready.
