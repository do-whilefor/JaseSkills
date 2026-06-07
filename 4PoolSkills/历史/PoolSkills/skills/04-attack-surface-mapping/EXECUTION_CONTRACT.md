# EXECUTION_CONTRACT：04-attack-surface-mapping

## 目的
汇总 HTTP/API/GraphQL/WebSocket/RPC/CLI/文件处理/上传下载/队列任务暴露面。

## 必须触发
- 用户要求暴露面、接口表、路由清单、API 攻击面、租户/管理员边界映射时必须触发

## 禁止触发
- 不得把前端发现的接口直接当作后端存在；必须标记 source 和验证状态

## 输入合同
- project_inventory.json
- code_graph.json
- js_asset_findings.json
- OpenAPI/GraphQL schema

## 输出合同
- outputs/attack_surface.json
- outputs/route_parameter_map.json
- outputs/boundary_map.json

## 必须调用的子模块
- `scripts/route_extractor.py`
- `scripts/js_asset_extractor.py`


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
- tests/adversarial_regression_cases.json: source_map_deprecated_api
- tests/adversarial_regression_cases.json: frontend_interface_backend_auth


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
