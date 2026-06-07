# REPORT_GENERATION_CONTRACT

## 硬性输入
- `outputs/evidence_manifest.json`
- `outputs/quality_gate_result.json`
- `outputs/security_graph.json`
- `report_templates/*.md`

## 生成规则
- confirmed 漏洞只能来自 manifest 中 `state=confirmed` 且 `quality_gate_result=pass` 的候选。
- `quality_gate_passed` 但未人工确认的候选进入“待确认漏洞”。
- `validation_blocked`、`needs_human_review`、`rejected` 只能进入“观察项/阻断项/误报项”。
- 每个报告结论必须引用：代码位置、请求/响应摘要、认证上下文、负样本、复现次数、影响范围、quality gate 评分、修复建议。
- 没有 evidence manifest 的结论不得进入“确认漏洞”。
