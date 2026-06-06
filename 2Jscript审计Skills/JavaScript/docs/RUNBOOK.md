# 运行手册

## 基础自检

```bash
python scripts/package_self_check.py .
python scripts/verify_js_top_tier_assets.py .
python scripts/js_unit_tests.py --root . --out tests/unit-last-run
```

Windows 推荐入口：

```powershell
npm run windows:check
npm run windows:validate
```

## 授权运行证据导入

运行证据目录必须来自授权目标，并包含 `artifact-origin.json`。fixture、sample、demo、synthetic 来源会被授权目标导入门槛阻断。

```bash
python scripts/js_runtime_artifact_importer.py --evidence-root <authorized-runtime-artifacts> --out reports/js-top-tier --require-authorized-target
python scripts/js_authorized_target_import_gate.py --evidence-root <authorized-runtime-artifacts> --out reports/js-top-tier
python scripts/js_top_tier_quality_gate.py --report-dir reports/js-top-tier
```

## 结论边界

静态分析、regex supplement、OSS static replay、browser replay plan 都不能单独支撑 verified。confirmed/verified 需要请求响应、运行证据、角色/租户或后端 acceptance 证据和质量门禁共同满足。
