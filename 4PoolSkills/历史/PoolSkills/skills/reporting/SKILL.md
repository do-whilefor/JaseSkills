# reporting

这是兼容性入口，不替代原有编号 Skill。原有 Skills 主体、原有知识库、原有漏洞模板、原有有效测试与原有有效脚本必须保留。

## 触发条件
当用户任务命中 `reporting` 对应能力，且目标为本机授权项目、开源靶场、测试环境或授权代码仓库时触发。未授权真实目标、破坏性验证、持久化、隐蔽控制、数据窃取、DoS 不触发。

## 授权和禁止条件
只处理本机路径、授权仓库、授权 HAR/Burp/Playwright 记录和用户明确允许的测试环境。禁止把静态候选写成 confirmed，禁止在没有 request/response、HAR、截图、日志、代码路径、AST/dataflow 之一时给严重漏洞定性，禁止对未授权目标发起验证。

## 输入要求
必须提供目标本机目录或已脱敏证据文件。动态验证必须额外提供 allowed_hosts、base_url、角色矩阵、租户矩阵、登录态或明确的 credential_ref。没有这些输入时输出 `needs_review` 或 `validation_blocked`。

## 输出要求
输出：candidate/inconclusive/confirmed report rendering only from evidence and quality results。所有输出必须包含文件路径、行号或 evidence id。不能输出未绑定证据的结论。

## 执行步骤
1. 读取 `config/skill_capability_bindings.json` 找到绑定实现。
2. 运行绑定脚本：tools/dashboard_builder.py, scripts/evidence_report_generator.py。
3. 将结果写入 `outputs/current/` 或用户指定 outdir。
4. 运行 schema 校验、quality gate 和 capability auditor。
5. 失败时保留错误、降级状态和复核原因。

## 失败处理
文件缺失、工具链缺失、schema 失败、动态运行失败、角色/租户矩阵缺失、证据不足时，状态只能为 `needs_review`、`blocked` 或 `validation_blocked`。不得补写假证据。

## 质量门槛
当前状态：静态发现只能是候选风险；是否确认由 evidence manifest 和 quality gate 决定。权限类、租户类、严重漏洞类必须有动态证据和负向控制后才能进入 confirmed 报告。

## 测试样例
```bash
python tools/selftest.py --root . --out outputs/current/selftest_result.json
python scripts/skill_selftest.py --root . --out outputs/current/skill_selftest_result.json
python scripts/capability_auditor.py --root . --out outputs/current/capability_audit.json
python scripts/severe_vuln_matrix_check.py --out outputs/current/severe_vuln_matrix_check.json
```

## 交接协议
本入口只把结果交给 evidence manifest、quality gate、dashboard、report mapping；没有通过 quality gate 的结果不得进入 confirmed 报告。

## 原始来源映射
绑定能力：09-reporting-disclosure + tools/dashboard_builder.py + scripts/evidence_report_generator.py。对应证明文件见 `config/skill_capability_bindings.json`、`manifests/CAPABILITY_PROMOTION_STATUS.json`。
