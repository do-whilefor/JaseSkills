# P0 Repair Summary 2026-06-06

本次修复目标：把 JS 渗透测试 Skills 从“文档和候选发现”升级为“证据优先、严格降级、可执行、可回放、可追责”的本机授权审计系统。

## 已完成的 P0 修复

1. AST backend 修复
   - `scripts/backends/js/babel_extract.mjs`
   - `scripts/backends/js/typescript_extract.mjs`
   - 修复 `.mjs` 内使用 `require` 导致 ESM 运行错误的问题。
   - `scripts/js_top_tier_analyze.py` 只在 AST backend 无错误且有语义产物时才允许 `semantic_status=ready`。

2. 质量门槛严格化
   - `scripts/js_top_tier_quality_gate.py` 升级为 v3。
   - `plan-only` 浏览器 replay 最高只给动态验证 5 分。
   - 缺少 runtime evidence、role/tenant replay、backend acceptance 时强制 blocking。
   - 缺少真实执行证据时总体分数封顶。

3. 自我审计严格化
   - `scripts/js_self_audit_matrix.py` 升级为 v2。
   - 不再把 `js_browser_replay_plan.json` 当作真实浏览器证据。
   - 必须检查 HAR、trace、截图、请求响应、role/tenant mapping、后端接受性证据。

4. 动态证据桥接加强
   - `scripts/js_runtime_evidence_bridge.py` 升级为 v2。
   - `ready` 必须同时满足 HAR、trace、截图、请求/响应元数据、role/tenant mapping。

5. 新增执行器与验证器
   - `scripts/js_playwright_safe_replay_executor.py`：只在明确 `--execute` 且授权环境可用时执行安全 Playwright replay。
   - `scripts/js_backend_acceptance_probe.py`：对 baseline 与 mutated 请求进行非破坏性对比，默认只允许 localhost / .local，除非显式 `--allow-external`。

6. 回归 runner 稳定化
   - `scripts/run_js_top_tier_fixture_tests.py` 改为进程内 runpy 执行，避免 subprocess 卡死。
   - 输出每一步 stdout/stderr、耗时、检查结果。

## 当前验收结果

- `package_self_check.py`：通过。
- `verify_js_top_tier_assets.py`：通过。
- `run_js_top_tier_fixture_tests.py`：通过。
- `js_quality_gate.json` 当前评分：42.2。
- 当前 verdict：`not-top-tier-until-p0-fixed`。

## 为什么仍然不能宣称 ready

因为当前压缩包内没有真实授权目标产生的：

- Playwright trace。
- 截图。
- 完整 HAR / Burp 请求响应。
- role/tenant mapping。
- 多角色 / 多租户授权结果。
- 后端接受隐藏参数的请求响应差异与安全影响证明。
- 真实 OSS replay 样本。

这不是脚本失败，而是正确降级。未导入真实执行证据前，只能声称“候选发现 + 严格证据门槛 + 可执行验证框架”。
