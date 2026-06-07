# EXECUTION_CONTRACT：10-regression-selftest-dashboard

## 目的
运行自测、对抗回放、健康度评分、dashboard 生成和索引一致性检查。

## 必须触发
- 用户要求验收、自检、回归、dashboard、持续进化检查时必须触发

## 禁止触发
- 禁止将未执行测试写成通过；不可执行必须标记 blocked/tool_missing/environment_missing

## 输入合同
- tests/*.json
- outputs/evidence_manifest.json
- outputs/security_graph.json
- outputs/quality_gate_result.json

## 输出合同
- outputs/regression_result.json
- outputs/tool_health_score.json
- dashboard/index.html

## 必须调用的子模块
- `scripts/adversarial_regression_runner.py`
- `scripts/tool_health_score.py`
- `scripts/dashboard_status_generator.py`
- `scripts/acceptance_check.py`


## 失败处理：降级但不降权
- 工具不可用时，输出 `status=degraded`、`tool_missing` 或 `environment_missing`，不得伪造工具结果。
- 缺少认证上下文、租户上下文、测试账号或动态工具时，候选只能停留在 `validation_blocked` 或 `needs_human_review`。
- 缺少代码证据、请求/响应证据、负样本或复现次数不足时，不得进入 `confirmed`。
- 降级路径只能减少自动化程度，不能降低证据门槛。

## Evidence manifest 写入规则
- 所有候选、路由、参数、代码位置、动态证据、负样本、截图、日志、quality gate 分数都必须写入 `outputs/evidence_manifest.json`。
- 未写入 manifest 的结论只能作为 observation，不得作为 confirmed vulnerability。
- 写入前必须通过 `scripts/evidence_manifest_validate.py`。

## Quality gate 进入规则
- 候选状态至少达到 `negative_control_passed` 才能进入 quality gate。
- `scripts/quality_gate_score.py` 返回 pass 且状态机合法，才允许进入 `quality_gate_passed`。
- 只有 `quality_gate_passed` 可由 09 skill 写成 confirmed 漏洞报告。

## Regression test 验证
- tests/adversarial_regression_cases.json


## 机器可校验字段
```json
{
  "contract_version": "audit-contract",
  "must_write_manifest": true,
  "must_pass_state_machine": true,
  "must_pass_quality_gate_before_confirmed": true,
  "non_destructive_only": true
}
```

## 执行加固补充

- confirmed 前必须调用 `scripts/quality_gate_hard_enforcer.py`。
- 链式风险必须调用 `scripts/chain_evidence_validator.py`，并写入 `chain_evidence_nodes`。
- 调用 23 类研究单元前，应检索 `ORIGINAL_TO_RESEARCH_UNIT_MAPPING.md` 与 `raw_original_kb_templates/`。
