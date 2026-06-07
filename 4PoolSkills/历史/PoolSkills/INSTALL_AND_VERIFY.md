# 安装与验收

```bash
cd authorized_security_audit_system
python3 tools/runtime_check.py --root . --out outputs/current/runtime_readiness.json
python3 tools/selftest.py --root . --out outputs/current/selftest_result.json
python3 tools/js_asset_extractor.py tests/fixtures/minimal_project --out outputs/current/js_assets.json
python3 tools/route_extractor.py tests/fixtures/minimal_project --out outputs/current/routes.json
python3 scripts/detectors/detector_runner.py tests/fixtures/minimal_project --out outputs/current/candidates.json
python3 tools/evidence_builder.py --root tests/fixtures/minimal_project --candidates outputs/current/candidates.json --out outputs/current/evidence_manifest.json
python3 tools/quality_gate.py --candidates outputs/current/candidates.json --evidence outputs/current/evidence_manifest.json --out outputs/current/quality_result.json
python3 tools/dashboard_builder.py --routes outputs/current/routes.json --js outputs/current/js_assets.json --candidates outputs/current/candidates.json --evidence outputs/current/evidence_manifest.json --quality outputs/current/quality_result.json --out dashboard/current/index.html
```

验收规则：schema 校验通过；fixture replay 通过；静态候选不得被 quality gate 提升为 confirmed；runtime missing 必须显示为 degraded，不能伪装 ready。
