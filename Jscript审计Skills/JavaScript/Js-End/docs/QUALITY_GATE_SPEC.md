# 统一质量门禁规范

## 强制格式

结论是否可交付：yes/no/partial  
不可交付原因：列出缺失输入、缺失证据、冲突或安全边界  
已满足条件：列出已经有证据支撑的条件  
未满足条件：列出阻断结论的条件  
证据来源：文件、请求、响应、日志、截图、manifest  
文档映射：对应原文阶段或字段  
风险等级：critical/high/medium/low/info/unknown  
需要人工确认：yes/no  
下一步动作：最小可执行补证动作

## 状态降级规则

- verified 缺任一关键证据 → insufficient_evidence。
- 只有工具告警 → candidate 或 false_positive。
- 只有报错 → insufficient_evidence 或 false_positive。
- 管理员权限、预期功能、所有用户可访问、无跨边界 → not_reportable。
- 环境缺失、账号缺失、证据目录缺失 → not_deliverable 或 candidate。


## Skills 极限评审质量门槛

- `ready` 必须同时有可执行文件、真实调用链、测试/fixture、证据输出和失败处理。
- `partial` 必须说明已实现部分与缺口，不能进入“顶级能力”结论。
- `doc-only` 必须明确“只有 Markdown/模板/说明，没有可执行实现”。
- `fake-ready` 必须作为 P0：声明 ready 但缺运行依赖、脚本不可执行、没有 runtime check 或测试。
- 没有文件路径、脚本名、函数名、schema 字段、模板名、测试用例名、fixture 名、dashboard 字段、manifest 字段或命令输出的结论必须标“未证实”。


## 第二轮反向审查质量门槛

- 文件证据缺失：结论必须降级为 `未证实`。
- 仅 Markdown/JSON 矩阵：能力必须降级为 `doc-only`。
- 仅 grep/regex/关键词：能力必须写 `candidate-only，不是语义审计`。
- 缺 Playwright/Burp/HAR 请求响应证据：漏洞状态必须写 `未动态验证`。
- 缺多角色/多租户 replay：越权、租户隔离、role-only chunk 相关结论必须写 `缺少 role/tenant replay`。
- 缺 positive/negative/blocked/needs_review 样本：测试状态必须写 `测试不足`。
- 修复项必须包含修改文件、新增文件、新增测试、执行命令、验收标准、失败回滚、保留知识库和漏洞模板的说明。


## Final Evidence Court Gate

第三层证据法庭 gate 由 `scripts/final_evidence_court_audit.py` 执行。硬性失败/降级规则：

- 未发现 AST backend：JS 审计状态必须为 missing/fake-ready risk。
- 未发现 Source Map parser：Source Map 能力必须为 partial/doc-only。
- 未发现 Playwright/Burp/HAR bridge：动态验证必须为未动态验证。
- 未发现 role/tenant replay：严重漏洞发现必须标注缺少 role/tenant replay。
- 未发现 detector registry：严重漏洞 detector 必须标注 candidate-only/doc-only。
- 未发现 schema validator：证据链必须标注证据不可强校验。
- 未发现 report generator：必须标注无法闭环到报告。
- 未发现 dashboard generator：必须标注展示层伪闭环。


## JS 顶级链路新增硬门槛

- `js_analysis.json.semantic_status != ready`：所有 source/sink/auth/tenant 结果不得超过 `candidate-only`。
- `js_runtime_evidence.json.status != ready`：动态验证不得 promoted。
- `js_role_tenant_diff.json.status != ready`：多角色/多租户严重漏洞链不得 promoted。
- `js_quality_gate.json.decision != promotable`：不得输出世界顶级 ready 结论。


## 2026-06-06 追加质量门槛

- 没有 `js_api_parameter_model.json`：隐藏接口/隐藏参数能力最高 35%。
- 没有 `js_backend_param_diff.json`：不得声称发现“前端不接受但后端接受”的参数。
- 没有 `js_browser_replay_plan.json` 或等价 HAR/trace：懒加载与真实浏览器交互最高 45%。
- 没有 `js_severe_candidate_map.json`：严重 JS 漏洞候选缺少验证链映射。
- 没有 `js_self_audit_matrix.json`：最终报告必须标记为自我追责未完成。
