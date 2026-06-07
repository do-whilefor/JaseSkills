# EXECUTION_CONTRACT：02-project-intelligence

## 目的
识别项目结构、语言、框架、配置、依赖、入口、运行方式。

## 必须触发
- 用户给出项目目录并要求结构分析、框架识别、配置/依赖识别时必须触发

## 禁止触发
- 没有本机路径、没有授权项目、只需单个报告润色时禁止触发

## 输入合同
- 项目根目录
- 可选环境说明
- package/lock/config/CI/Docker 文件

## 输出合同
- outputs/project_inventory.json
- outputs/framework_fingerprint.json
- outputs/dependency_inventory.json

## 必须调用的子模块
- `scripts/project_inventory.py`
- `config/toolchain_requirements.json`


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
- tests/regression_cases.json


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
