# EXECUTION_CONTRACT：01-authorized-maximum-orchestrator

## 目的
作为本机授权安全审计系统总入口，确认边界、分发任务、串联 evidence manifest 与 quality gate。

## 必须触发
- 用户请求完整授权项目审计、漏洞验证、报告生成、跨 skill 编排时必须触发
- 任何涉及高危漏洞确认前必须经过本入口的状态机约束

## 禁止触发
- 非授权第三方目标、MITM、DoS、破坏性写入、真实第三方数据访问
- 用户只询问安装/解释且不要求执行审计时不得强制触发

## 输入合同
- 授权范围说明
- 项目路径
- 审计目标
- 允许工具清单
- 现有 evidence manifest

## 输出合同
- outputs/run_context.json
- outputs/orchestration_plan.json
- outputs/candidate_registry.json
- outputs/final_status.json

## 必须调用的子模块
- `config/core_skill_routing.json`
- `config/candidate_state_machine.json`
- `scripts/evidence_manifest_validate.py`
- `scripts/quality_gate_score.py`


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
- tests/adversarial_regression_cases.json: empty_directory_task
- tests/adversarial_regression_cases.json: prompt_injection_in_readme


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
