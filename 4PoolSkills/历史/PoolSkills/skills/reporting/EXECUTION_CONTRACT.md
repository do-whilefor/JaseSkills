# Execution Contract: reporting

- 仅在本机授权目标、测试样本或 Skills 自检中执行。
- 输出不得从静态候选直接提升为 confirmed。
- 所有漏洞结论必须绑定文件、行号、证据 id 或 evidence manifest 条目。
- 工具不可用、scope 缺失、schema 失败、动态证据缺失或角色/租户矩阵不足时，状态只能为 candidate、needs_review、blocked 或 inconclusive。
- 报告生成前必须经过 evidence/ref_validator.py 与 quality/quality_gate.py。
