# v3 增强报告

## 新增能力

1. Claude Code 端到端触发回放测试。
2. 100 条真实结构的合成 SecKB 样本集，用于压测 quality gate。
3. 索引一致性检查，校验记录、模板、master-index、template-index 的互相引用。
4. 静态 HTML dashboard，显示来源可信度、freshness、冲突和人工确认队列。
5. 模板混淆矩阵，覆盖 SSRF vs URL fetch、RCE vs 命令执行危险函数、信息泄露 vs 可报告敏感数据暴露、IDOR vs 正常权限差异。

## 原则

- 不降低 v2 原有能力。
- 不新增攻击性验证逻辑。
- 不把合成样本当真实漏洞。
- 不声称已经联网采集。
- 所有新内容均为“基于文档延伸”，用于测试、治理和稳定性增强。

## 验收命令

```powershell
python .\scripts\claude_code_replay.py .	ests\claude-code-replayeplay-cases.json .eports\claude-code-replay-dryrun.json
python .\scripts\quality_gate_stress.py
python .\scripts\check_index_consistency.py .	estdata\index-consistency --output .eports\index-consistency.json
python .\scripts\dashboard_build.py .	estdata\quality-gateecords_100.json .eports\dashboard.html --format html
python .\scripts	emplate_confusion_test.py
python .\scripts\self_audit_skills.py . .eports\self-audit-v3.json
python .\scripts\smoke_test_package.py . .eports\smoke-test-v3.json
```
