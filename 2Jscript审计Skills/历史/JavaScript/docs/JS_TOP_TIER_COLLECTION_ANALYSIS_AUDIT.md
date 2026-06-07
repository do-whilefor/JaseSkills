# JS 顶级收集、分析、审计工程链路

本链路以可执行产物为准：资产账本、分析结果、finding、runtime evidence、role/tenant diff、quality gate。

## 最小可运行命令

```bash
python scripts/js_top_tier_collect.py --root fixtures/js-top-tier-samples/app --out tests/js-top-tier-last-run
python scripts/js_top_tier_analyze.py --ledger tests/js-top-tier-last-run/js_asset_ledger.json --out tests/js-top-tier-last-run
python scripts/js_top_tier_quality_gate.py --report-dir tests/js-top-tier-last-run
```

## 降级原则

- 无真实 AST backend：candidate-only。
- 无 HAR/trace/screenshot：未动态验证。
- 无多角色/多租户 ledgers：缺少 role/tenant replay。
- 无 schema/report mapping：证据链不闭环。

## 可选增强命令

```bash
python scripts/js_runtime_evidence_bridge.py --evidence-root <har-trace-screenshot-dir> --out reports/js-top-tier
python scripts/js_role_tenant_diff.py --input user=<user-report-dir> --input admin=<admin-report-dir> --out reports/js-top-tier
```
