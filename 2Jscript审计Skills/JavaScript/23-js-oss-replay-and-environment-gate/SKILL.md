# 23 JS OSS Replay and Environment Gate

## Trigger
Use before claiming the JS audit system is reusable, stable, or ready.

## Execution
1. Run `python scripts/install_and_env_check.py --root . --out reports/env-check`.
2. Import or clone authorized real OSS samples into `fixtures/oss-replay/<sample>/`.
3. For each sample, add source, license note, setup/start commands, replay manifest, evidence manifest, expected positive/negative/blocked/needs_review cases.
4. Run `scripts/js_oss_replay_registry.py` and `scripts/run_js_top_tier_fixture_tests.py`.
5. Run quality gate and self-audit.

## Blocking condition
Fewer than 10 real OSS replay samples means the package cannot claim broad top-tier generalization. Registry-only samples do not count as real replay.
