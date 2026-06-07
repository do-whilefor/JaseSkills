# DASHBOARD_DATA_CONTRACT

Dashboard 必须只读取真实数据源，不得展示硬编码成功结果。

## 数据源
- `outputs/evidence_manifest.json`
- `outputs/security_graph.json`
- `outputs/quality_gate_result.json`
- `outputs/regression_result.json`
- `outputs/tool_health_score.json`

## 链路展示
Route → Handler → Guard → Actor → Asset → Trust Boundary → Candidate → Evidence → Quality Gate → Report Section

## 缺失处理
- 数据源缺失：展示 `blocked`。
- 工具缺失：展示 `tool_missing`。
- 未运行测试：展示 `not_run`。
- 不允许默认展示 pass。
