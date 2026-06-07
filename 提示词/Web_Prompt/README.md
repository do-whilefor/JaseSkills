# Web 安全验证 Prompt 包

用途：只针对“本地搭建的 Web 页面 / Web 服务”进行动态安全验证，不包含本地源码、依赖、语言栈、worker、CLI 等项目代码审计内容。

建议使用顺序：

1. `00_web_master_prompt.md`
2. `01_web_facts_baseline.md`
3. `02_browser_validation_baseline.md`
4. `03_web_exposure_matrix.md`
5. `04_high_priority_web_validation.md`
6. `05_dynamic_validation_matrix.md`
7. `06_browser_special_checks.md`
8. `07_web_impact_path.md`
9. `08_self_review_second_round.md`
10. `09_uncommon_web_checks.md`
11. `10_final_web_report.md`
12. `11_evidence_cleaning.md`
13. `12_next_round.md`
14. `13_rebel_review_patch.md`

`ALL_IN_ONE_WEB_PROMPT.md` 是完整合并版，可直接复制给 Claude。

措辞原则：

- “漏洞挖掘”改为“安全验证 / 高影响缺陷验证”。
- “0day”改为“未知高影响缺陷候选”。
- “攻击链”改为“影响路径”。
- “利用”改为“动态复核 / 非破坏性验证”。
- “绕过”改为“边界失效 / 权限不一致”。
- “payload”改为“测试输入 / 输入变体”。
- “爆破 / 打穿”改为“矩阵化验证 / 差异对照 / 端到端影响确认”。

核心质量门槛：没有真实浏览器动作、network 请求、actor 对照、权限边界、证据、复现、断言、修复建议和回归测试，不得写 confirmed。
