# Js-End Authorized JS Audit Skills

版本：`2026.06.06-clean1`

这是一个面向授权 JS / 前端 / Node.js / Web 项目的证据优先安全审计 Skills 包。它保留原有知识库与漏洞模板，并补充 JS 资产收集、AST/语义候选解析、API/参数建模、Playwright/CDP replay 编排、HAR/trace/screenshots evidence manifest、GraphQL/WebSocket runtime replay、后端接受性验证、role/tenant 矩阵、质量门禁和 dashboard drill-down。

## 安装

将压缩包解压到 Claude Skills 根目录。Windows 示例：

```powershell
Expand-Archive .\Js-End-world-top-clean-20260606.zip -DestinationPath $env:USERPROFILE\.claude\skills -Force
```

安装后目录应类似：

```text
%USERPROFILE%\.claude\skills\Js-End\SKILL.md
```

Linux / macOS 示例：

```bash
unzip Js-End-world-top-clean-20260606.zip -d ~/.claude/skills
```

## 入口

优先读取：

```text
Js-End/SKILL.md
Js-End/00-js-master-dispatcher/SKILL.md
Js-End/01-js-scope-evidence-quality-gate/SKILL.md
```

## 保留内容

本清理版保留：

- `knowledge/`：原有知识库与新增 JS 审计知识库。
- `templates/`：原有漏洞模板与新增 evidence / runtime / backend acceptance / business flow 模板。
- `data/`：规则数据、能力矩阵和降级规则。
- `schemas/`：evidence manifest、runtime evidence、API 参数模型、quality gate 等 schema。
- `fixtures/`：可复用 fixture、OSS replay registry 样本骨架和正/负/阻断/复核样本。
- `scripts/`：收集、分析、验证、报告、dashboard、自检脚本。
- `tests/`：回归测试配置与样本 manifest。

已清理：`__pycache__`、`.pyc`、`.pytest_cache`、`.DS_Store`、`Thumbs.db`、临时日志、运行态 `reports/`、上次生成的 `tests/js-top-tier-last-run/`。

## 一键检查

```bash
python scripts/package_self_check.py .
python scripts/verify_js_top_tier_assets.py .
python scripts/install_and_env_check.py --root . --out reports/env-check
```

## Fixture 回归

```bash
python scripts/run_js_top_tier_fixture_tests.py .
```

该命令会重新生成 `tests/js-top-tier-last-run/`。这个目录是运行产物，不随清理版压缩包保留。

## 授权项目审计运行顺序

```bash
python scripts/js_top_tier_collect.py --root <frontend-or-build-root> --out reports/js-top-tier
python scripts/js_top_tier_analyze.py --ledger reports/js-top-tier/js_asset_ledger.json --out reports/js-top-tier
python scripts/js_wrapper_resolver.py --root <frontend-root> --out reports/js-top-tier
python scripts/js_api_parameter_model.py --ledger reports/js-top-tier/js_asset_ledger.json --root <frontend-or-build-root> --backend-root <optional-backend-root> --out reports/js-top-tier
python scripts/js_backend_param_diff.py --api-model reports/js-top-tier/js_api_parameter_model.json --out reports/js-top-tier
python scripts/js_browser_lazyload_replay_plan.py --url <authorized-local-url> --out reports/js-top-tier
python scripts/js_playwright_safe_replay_executor.py --plan reports/js-top-tier/js_browser_replay_plan.json --generate-spec --out reports/js-top-tier
python scripts/js_runtime_evidence_manifest.py --evidence-root <har-trace-screenshot-dir> --out reports/js-top-tier
python scripts/js_role_tenant_diff.py --input user=<user-report-dir> --input admin=<admin-report-dir> --out reports/js-top-tier
python scripts/js_backend_acceptance_probe.py --input <probe-plan.json> --out reports/js-top-tier
python scripts/js_graphql_ws_runtime_replay.py --scenarios <graphql-ws-scenarios.json> --out reports/js-top-tier
python scripts/js_schema_alignment.py --root <repo-root> --api-model reports/js-top-tier/js_api_parameter_model.json --out reports/js-top-tier
python scripts/js_sourcemap_reconstructor.py --root <frontend-root> --out reports/js-top-tier/sourcemap-reconstructed
python scripts/js_service_worker_cache_auditor.py --root <frontend-root> --out reports/js-top-tier
python scripts/js_cdn_history_asset_enumerator.py --ledger reports/js-top-tier/js_asset_ledger.json --out reports/js-top-tier
python scripts/js_framework_build_parser.py --root <frontend-root> --out reports/js-top-tier
python scripts/js_hidden_feature_extractor.py --root <frontend-root> --out reports/js-top-tier
python scripts/js_business_flow_template_generator.py --out reports/js-top-tier
python scripts/js_severe_js_candidate_mapper.py --api-model reports/js-top-tier/js_api_parameter_model.json --param-diff reports/js-top-tier/js_backend_param_diff.json --out reports/js-top-tier
python scripts/js_evidence_dashboard_drilldown.py --report-dir reports/js-top-tier
python scripts/js_top_tier_report_generator.py --report-dir reports/js-top-tier
python scripts/js_top_tier_quality_gate.py --report-dir reports/js-top-tier
python scripts/js_self_audit_matrix.py --root . --report-dir reports/js-top-tier
```

## 强制降级规则

- `js_browser_replay_plan.json` 只是计划，不是运行证据。
- 没有 HAR、trace、screenshots、request/response evidence manifest 时，不得把漏洞写成 verified。
- 没有 role/tenant replay 时，不得声称完成越权、多租户隔离或权限绕过验证。
- 没有 `accepted-and-impactful` 的后端接受性证据时，不得声称后端接受隐藏参数并产生安全影响。
- registry-only OSS 样本不计入真实 OSS replay。
- 缺动态证据时，严重漏洞最高只能是 `candidate-only / needs_review`。

## 版本说明

详见：

```text
CHANGELOG.md
RELEASE_NOTES.md
RELEASE_MANIFEST.json
```
