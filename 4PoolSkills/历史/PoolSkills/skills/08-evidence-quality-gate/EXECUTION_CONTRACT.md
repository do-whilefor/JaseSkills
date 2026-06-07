# EXECUTION_CONTRACT：08-evidence-quality-gate

## 目的
校验证据 schema、状态机、三次复现、负样本、评分和报告准入。

## 必须触发
- 任何候选进入 reproduced、quality_gate_passed、confirmed 或报告前必须触发

## 禁止触发
- 缺少 manifest、缺负样本、缺认证上下文、缺影响证明时不得通过

## 输入合同
- EVIDENCE_MANIFEST_SCHEMA.json
- outputs/evidence_manifest.json
- config/candidate_state_machine.json

## 输出合同
- outputs/quality_gate_result.json
- outputs/rejected_candidates.json
- outputs/needs_human_review.json

## 必须调用的子模块
- `scripts/evidence_manifest_validate.py`
- `scripts/quality_gate_score.py`
- `scripts/state_machine_validate.py`


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
- tests/fixtures/quality_gate_pass.json
- tests/fixtures/quality_gate_fail_missing_negative.json


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
