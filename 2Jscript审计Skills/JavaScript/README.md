# Js-End Authorized JS Audit Skills

这是一个面向授权 JS / 前端 / Node.js / Web 项目的证据优先安全审计 Skills 包。它保留 `knowledge/` 知识库和 `templates/` 漏洞模板，核心目标是把静态候选、运行证据、质量门禁和最终报告分开处理，避免把缺证据的候选误写成已验证漏洞。

## Windows 运行方式

Windows 上优先使用 Node 跨平台 runner 或 PowerShell 包装器，不依赖 `bash`、Linux `timeout` 或固定的 `python3` 命令名。

```powershell
npm run windows:check
npm run windows:validate
powershell -ExecutionPolicy Bypass -File .\tools\windows\validate.ps1
```

`windows:validate` 只验证包结构、脚本入口、schema、确定性 fixture 和降级边界。真实漏洞确认仍必须导入授权目标的 HAR、trace.zip、截图、DOM snapshot、console log、request/response、GraphQL/WebSocket/postMessage frame 以及 role/tenant matrix。

## 安装

将完整压缩包解压到 Claude Skills 根目录。Windows 示例：

```powershell
Expand-Archive .\Js-End.zip -DestinationPath $env:USERPROFILE\.claude\skills -Force
```

解压后目录应类似：

```text
%USERPROFILE%\.claude\skills\Js-End\SKILL.md
```

Linux / macOS 示例：

```bash
unzip Js-End.zip -d ~/.claude/skills
```

## 入口

优先读取：

```text
Js-End/SKILL.md
Js-End/00-js-master-dispatcher/SKILL.md
Js-End/01-js-scope-evidence-quality-gate/SKILL.md
```

涉及 HAR/trace/screenshots、GraphQL/WebSocket runtime replay、schema 对齐、sourcemap 还原、service worker cache、framework build artifact、OSS replay 或环境自检时，继续读取 `21` 至 `23` 号 Skill。

## 保留内容

本清理版保留：

- `knowledge/`：知识库与 JS 审计知识条目。
- `templates/`：漏洞报告模板、evidence manifest 模板、runtime/backend/business-flow 模板。
- `data/`：规则数据、能力矩阵和降级规则。
- `schemas/`：evidence manifest、runtime evidence、API 参数模型、quality gate 等 schema。
- `fixtures/`：可复用 fixture、OSS replay registry 样本骨架和正/负/阻断/复核样本。
- `scripts/`：收集、分析、验证、报告、dashboard、自检脚本。
- `tests/`：回归测试配置与样本 manifest。

已清理：发布说明、版本号文件、构建差异说明、一次性修复记录、运行态 `reports/`、`test-results/`、上次生成的验证输出和含本机绝对路径的测试结果。

## 自检命令

```bash
python scripts/package_self_check.py .
python scripts/verify_js_top_tier_assets.py .
node scripts/js_cross_platform_runner.mjs windows:validate
python scripts/js_unit_tests.py --root . --out tests/unit-last-run
```

## 授权项目审计顺序

```bash
python scripts/js_top_tier_collect.py --root <frontend-or-build-root> --out reports/js-top-tier
python scripts/js_top_tier_analyze.py --ledger reports/js-top-tier/js_asset_ledger.json --out reports/js-top-tier
python scripts/js_semantic_graph_builder.py --root <frontend-or-build-root> --ledger reports/js-top-tier/js_asset_ledger.json --out reports/js-top-tier
python scripts/js_api_parameter_model.py --ledger reports/js-top-tier/js_asset_ledger.json --root <frontend-or-build-root> --backend-root <optional-backend-root> --out reports/js-top-tier
python scripts/js_backend_param_diff.py --api-model reports/js-top-tier/js_api_parameter_model.json --out reports/js-top-tier
python scripts/js_browser_lazyload_replay_plan.py --url <authorized-local-url> --out reports/js-top-tier
python scripts/js_playwright_safe_replay_executor.py --plan reports/js-top-tier/js_browser_replay_plan.json --generate-spec --execute --out reports/js-top-tier
python scripts/js_runtime_artifact_importer.py --evidence-root <authorized-runtime-artifacts> --out reports/js-top-tier --require-authorized-target
python scripts/js_authorized_target_import_gate.py --evidence-root <authorized-runtime-artifacts> --out reports/js-top-tier
python scripts/js_role_tenant_authorization_replay.py --matrix <role-tenant-matrix.json> --out reports/js-top-tier
python scripts/js_runtime_detector_binder.py --detectors reports/js-top-tier/js_detector_registry_run.json --runtime-bundle reports/js-top-tier/js_runtime_artifact_bundle.json --authorization reports/js-top-tier/js_role_tenant_authorization_result.json --out reports/js-top-tier
python scripts/js_top_tier_quality_gate.py --report-dir reports/js-top-tier
python scripts/js_top_tier_report_generator.py --report-dir reports/js-top-tier
```

## 强制降级规则

`js_browser_replay_plan.json` 只是计划，不是运行证据。没有 HAR、trace、screenshots、request/response、role/tenant replay、backend acceptance 和 evidence manifest 时，不得把漏洞写成 verified。fixture、sample、demo、synthetic evidence 不能满足授权目标导入门槛。
