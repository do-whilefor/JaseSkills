# js-domxss-detector

用途：授权范围内的 JS 审计子能力。所有输出必须绑定 evidence manifest；静态证据只能输出 candidate / needs_review。

输入格式：scope JSON、资产根目录或运行证据目录；需要时读取 ledger、semantic graph、HAR、trace、screenshot、DOM snapshot。

输出格式：JSON artifact，包含 schema_version、status、evidence、promotion_blockers；报告映射到 templates/。

CLI：`python3 scripts/js_detector_registry_runner.py --graph <graph> --ledger <ledger> --scope <scope> --out <report-dir>`

错误处理：scope 缺失、schema 非法、secret 未脱敏、confirmed 缺 request/response、越权缺多角色或多租户验证时直接 FAIL。

Evidence manifest 绑定：每条 finding 必须记录 source file、line、AST/provenance、request/response 或 runtime artifact；否则不得进入正式 confirmed 报告。

Quality gate 绑定：由 `scripts/js_top_tier_quality_gate.py` 和 `scripts/js_detector_registry_runner.py` 执行 promotion blocker。

测试样例：正样本、负样本、blocked、needs_review 的索引见 `data/js_detector_registry_v2.json` 与 `fixtures/adversarial-js-hallucination/`。

边界：仅用于本机、授权项目、开源项目、靶场、测试环境；禁止破坏性利用流程。
