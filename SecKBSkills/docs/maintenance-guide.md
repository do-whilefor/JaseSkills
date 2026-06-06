# 维护者说明（v2）

## 修改原则

1. 不得降低原始文档能力。
2. 不得删除原始文档安全边界。
3. 不得把延伸内容伪装为原文档内容。
4. 不得新增未说明来源的工具、路径或外部依赖。
5. 修改任何 SKILL.md 后，必须运行 `scripts/self_audit_skills.py`。
6. 修改模板或 schema 后，必须运行 `scripts/quality_gate.py` 的样例检查。
7. 修改路由规则后，必须运行 `scripts/rag_route_tests.py`。

## 版本记录要求

每次修改必须记录：

- 修改日期。
- 修改文件。
- 修改原因。
- 是否改变原文档能力。
- 是否属于基于文档延伸。
- 兼容性风险。
- 回滚方法。

## 禁止修改

以下内容不得删除：

- SecKB 固定根目录。
- 授权边界。
- 禁止 MITM。
- 禁止未授权第三方验证。
- promoted 质量门槛。
- 不可报告原因。
- prompt injection 隔离规则。
- SRC 官方规则优先。

## v3 修改后必须运行

```powershell
python .\scripts\claude_code_replay.py .	ests\claude-code-replayeplay-cases.json .eports\claude-code-replay-dryrun.json
python .\scripts\quality_gate_stress.py
python .\scripts\check_index_consistency.py .	estdata\index-consistency --output .eports\index-consistency.json
python .\scripts\dashboard_build.py .	estdata\quality-gateecords_100.json .eports\dashboard.html --format html
python .\scripts	emplate_confusion_test.py
python .\scripts\smoke_test_package.py . .eports\smoke-test-v3.json
```
