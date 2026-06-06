# JS 顶级收集/分析/审计报告模板

## 1. 输入与授权边界

- 授权范围：
- 输入目录/HAR/trace：
- 不允许动态验证的目标：

## 2. 资产账本

引用 `reports/js-top-tier/js_asset_ledger.json`。

必须列出：path、kind、source、sha256、size、mime、source map、manifest、worker、HAR 证据。

## 3. Parser backend 状态

引用 `reports/js-top-tier/js_analysis.json.backend_status`。

缺失 Node/Babel/tree-sitter 时，必须写：`candidate-only，不是语义审计`。

## 4. 严重漏洞候选

引用 `reports/js-top-tier/js_findings.json`。

每条 finding 必须包含：finding_id、rule_id、status、asset_path、evidence_path、line、backend、source、sink、dynamic_validation、role_tenant_replay、report_section、reason。

## 5. 动态验证与 role/tenant replay

没有 Playwright/Burp/HAR/trace/request-response/screenshot 时，必须写：`未动态验证`。
没有多角色、多租户对比时，必须写：`缺少 role/tenant replay`。

## 6. 质量门槛

引用 `reports/js-top-tier/js_quality_gate.json`。

不得绕过 caps 和 blocking。
