# EXECUTION_CONTRACT：06-dynamic-browser-burp-mcp

## 目的
以 Playwright/浏览器/Burp/MCP/HAR 采集非破坏性动态证据。

## 必须触发
- 用户要求动态验证、浏览器业务流、Burp 联动、HAR 采集、截图证据时必须触发

## 禁止触发
- 工具缺失时不得伪造请求/响应；禁止 DoS、删除、破坏性状态变更、第三方目标

## 输入合同
- validation_plan.json
- auth_contexts.json
- 测试账号
- 本机服务地址
- 工具健康度

## 输出合同
- outputs/dynamic_evidence/*.json
- outputs/har/*.har
- outputs/screenshots/*
- outputs/logs/*

## 必须调用的子模块
- `scripts/tool_health_score.py`
- `scripts/dynamic_validation_plan.py`
- `playbooks/DYNAMIC_VALIDATION_CLOSED_LOOP.md`


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
- tests/adversarial_regression_cases.json: only_error_no_impact
- tests/adversarial_regression_cases.json: three_reproduction_failed


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
