# EXECUTION_CONTRACT：05-js-audit-runtime

## 目的
收集、解析、回流 JS/SourceMap/API/签名函数/前端权限和运行时请求。

## 必须触发
- 用户要求 JS 审计、前端资源、source map、bundle、隐藏接口、签名函数时必须触发

## 禁止触发
- 不得把 JS 暴露信息直接确认为漏洞；必须回流到 attack surface 并经动态验证

## 输入合同
- HTML 页面
- 静态资源目录
- URL 清单
- source map
- bundle 文件

## 输出合同
- outputs/js_asset_findings.json
- outputs/js_discovered_endpoints.json
- outputs/js_security_observations.json

## 必须调用的子模块
- `scripts/js_asset_extractor.py`
- `rules/JS_ASSET_AUDIT_RULES.md`


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
