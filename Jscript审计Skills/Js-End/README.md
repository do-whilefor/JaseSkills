# JS Audit Skills

这是用于授权 JS / Node.js / 前端项目安全审计的 Claude Skills 包。它保留静态审计、动态验证、反向审查、证据门禁、JS 收集、JS 分析、JS 审计、报告输出和自检回放能力。

## 安装

将本目录放入 Claude Skills 根目录。Windows 示例：

```powershell
Expand-Archive .\Js-End-cleaned.zip -DestinationPath $env:USERPROFILE\.claude\skills -Force
```

安装后目录应类似：

```text
%USERPROFILE%\.claude\skills\Js-End\SKILL.md
```

## 主入口

优先从 `00-js-master-dispatcher` 进入。执行任何审计、复现、证据整理或报告任务前，先经过 `01-js-scope-evidence-quality-gate` 确认授权边界、输入范围和质量门槛。

## 核心能力

- 项目结构、语言、入口、路由、运行链路和信任边界分析。
- 参数、source-to-sink、鉴权、授权、租户、角色和敏感 sink 候选图谱。
- 配置、依赖、框架、供应链和前端构建暴露面分析。
- JS asset、manifest、chunk、dynamic import、Source Map、Service Worker、Worker、WASM、GraphQL、WebSocket、postMessage、storage、公开环境变量和 HAR 线索收集。
- 高危 JS 漏洞候选挖掘、动态验证计划、证据 manifest、质量门禁和最终报告。
- Skills 包自身的反向审查、二次反查、证据法庭降级和 JS 顶级链路自检。

## 运行命令

基础自检：

```bash
python scripts/package_self_check.py .
python scripts/skill_trigger_tester.py
python scripts/strict_quality_gate.py tests/sample-manifests/insufficient.json
```

专项资产自检：

```bash
python scripts/verify_extreme_review_assets.py .
python scripts/verify_second_pass_assets.py .
python scripts/verify_final_court_assets.py .
python scripts/verify_js_top_tier_assets.py .
```

JS 收集、分析、质量门禁示例：

```bash
python scripts/js_top_tier_collect.py --root fixtures/js-top-tier-samples/app --out tests/js-top-tier-last-run
python scripts/js_top_tier_analyze.py --ledger tests/js-top-tier-last-run/js_asset_ledger.json --out tests/js-top-tier-last-run
python scripts/js_top_tier_quality_gate.py --report-dir tests/js-top-tier-last-run
```

可选运行态证据桥接：

```bash
python scripts/js_runtime_evidence_bridge.py --evidence-root <har-trace-screenshot-dir> --out reports/js-top-tier
python scripts/js_role_tenant_diff.py --input user=<user-report-dir> --input admin=<admin-report-dir> --out reports/js-top-tier
```

## 证据规则

静态发现只能作为 candidate。`verified` 必须同时具备代码证据、真实请求/响应、三次复现、反证、影响证明、非破坏性记录和 manifest 质量门禁。缺少 runtime evidence、role/tenant replay、AST backend 或 schema 校验时，必须降级为 `candidate-only`、`partial`、`doc-only`、`insufficient_evidence` 或 `not_deliverable`。

## 保留内容

本清理版保留 `knowledge/`、`templates/`、所有子 Skill、schemas、data、fixtures、scripts 和 tests 中的可复用测试资产。已移除历史运行产物、升级/修复说明和与正常使用无关的临时报告。
