# 本机授权安全审计 Skills

本包用于明确授权范围内的本机代码仓库、靶场、开源测试项目和 Skills 自检。它执行静态采集、语义图构建、候选风险发现、非破坏性动态验证、证据归档、质量门禁和报告生成。

硬边界：

- 只处理用户明确授权的目标。
- detector 输出默认为 candidate，不等同于已确认漏洞。
- fixture、自检和示例结果不得替代真实目标证据。
- 严重风险要进入 confirmed，必须具备 schema-valid evidence manifest、可读脱敏证据、动态请求/响应证据、截图或 DOM 证据、负向控制、阻断控制记录，以及需要时的非占位角色/租户矩阵。
- Playwright replay JSON 不是独立证据；其中的 request、response、screenshot、DOM、HAR、trace、console 引用必须 stitch 到 evidence manifest，并且文件必须位于 manifest root 内。

核心目录：

- `common/`：scope、路径、网络、脱敏与安全边界。
- `collectors/`：路由、JS 资产、隐藏参数、依赖和 IaC 采集。
- `analyzers/`：语义图、跨文件关联、taint 路径。
- `detectors/`：候选风险规则与 typed taint detector。
- `dynamic/`：replay plan、Playwright replay、GraphQL、WebSocket、evidence stitching。
- `evidence/`：manifest 构建、哈希、脱敏、引用完整性校验。
- `quality/`：confirmed 质量门禁。
- `report/` 和 `report_templates/`：报告生成与漏洞报告模板。
- `knowledge/`、`raw_original_kb_templates/`、`vulnerability_templates/`、`vulnerability_research_units/`：保留的知识库和漏洞模板。

安装依赖：

```bash
python -m pip install -r requirements.txt
npm install
```

需要动态浏览器 replay 时，另外安装 Chromium：

```bash
python -m playwright install chromium
```

核心自检：

```bash
python run_engine_selftest.py
python -m pytest -q tests
```

本机授权目标扫描示例：

```bash
python collectors/route_collector.py <authorized_project> --out outputs/current/routes.json
python collectors/js_asset_collector.py <authorized_project> --out outputs/current/js_assets.json
python collectors/hidden_parameter_collector.py <authorized_project> --out outputs/current/params.json
python analyzers/semantic_graph_builder.py <authorized_project> --routes outputs/current/routes.json --params outputs/current/params.json --out outputs/current/security_graph.json
python analyzers/taint_engine.py --graph outputs/current/security_graph.json --out outputs/current/taint_paths.json
python detectors/detector_runner.py <authorized_project> --graph outputs/current/security_graph.json --out outputs/current/findings.json
python dynamic/candidate_to_replay_plan.py --candidates outputs/current/findings.json --out outputs/current/replay_plan.json
python evidence/evidence_manifest_builder.py --root <authorized_project> --candidates outputs/current/findings.json --out outputs/current/evidence_manifest.json
python dynamic/playwright_runner.py --plan outputs/current/replay_plan.json --root <authorized_project> --out outputs/current/replay_result.json
python quality/quality_gate.py --candidates outputs/current/findings.json --evidence outputs/current/evidence_manifest.json --replay outputs/current/replay_result.json --out outputs/current/quality_result.json
python report/report_generator.py --candidates outputs/current/findings.json --evidence outputs/current/evidence_manifest.json --quality outputs/current/quality_result.json --out outputs/current/security_report.md
```

Windows 入口：

```powershell
python -m pip install -r requirements.txt
npm install
python -m playwright install chromium
powershell -ExecutionPolicy Bypass -File .\windows\run_skills.ps1 -TargetRoot C:\path\to\authorized\repo
```

目标仓库存在 `scope.yaml` 时会自动使用；不存在时使用内存中的目标本地默认 scope，不向目标仓库写入配置文件。需要显式 scope 时传入 `-ScopeFile`。

可选 parser：

- PHP：安装 `nikic/php-parser` 或 tree-sitter PHP grammar 后才计为完整 AST；不可用时返回 `parser_unavailable` 或降级状态。
- Rust：安装 Rust AST bridge 或 tree-sitter Rust grammar 后才计为完整 AST；不可用时返回 `parser_unavailable` 或降级状态。
- JS/TS：Node 依赖用于 AST、sourcemap 和 chunk lineage。
