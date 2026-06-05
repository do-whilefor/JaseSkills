# Version Changelog

## v2.0-audited

变更类型：基于文档延伸 + 保真度修复。

### 新增

- `CAPABILITY_INDEX.md`：全局能力索引和触发仲裁。
- `docs/v2-aggressive-audit-report.md`：攻击性审计报告。
- `docs/document-fingerprint-matrix.md`：文档能力指纹矩阵。
- `docs/quality-gate-policy.md`：质量门禁策略。
- `docs/anti-hallucination-policy.md`：反幻觉规则。
- `docs/maintenance-guide.md`：维护者说明。
- `docs/extension-register.md`：延伸内容登记。
- `examples/failure-case-library.md`：失败案例库。
- `examples/absence-tests.md`：缺席测试。
- `templates/non-deliverable-reasons.md`：不可交付原因模板。
- `templates/negative-evidence-ledger.md`：负证据账本模板。
- `templates/learning-run-summary.md`：联网学习输出模板。
- `templates/audit-run-summary.md`：反向审计输出模板。
- `templates/source-confidence-rubric.md`：来源可信度评分模板。
- `scripts/self_audit_skills.py`：Skill 结构自审脚本。
- `scripts/smoke_test_package.py`：包完整性冒烟测试。

### 修复

- 强化 01 总控调度，避免子 Skill 争抢。
- 强化 `record.schema.json` required 字段。
- 强化 `quality_gate.py` promoted 门槛。
- 强化 RAG 负样本测试。
- 所有 SKILL.md 增加最小/标准/专家三档路径。

### 未改变

- 不改变原始安全边界。
- 不扩大动态验证到未授权目标。
- 不加入攻击性验证脚本。
- 不声称联网采集已完成。

## v3 - trigger replay, quality stress, index consistency, HTML dashboard, confusion matrix

- Added Claude Code replay cases for empty, fuzzy, negative, misfire and framework-confusion tasks.
- Added 100 synthetic SecKB records for quality gate stress testing.
- Added index consistency checker for records, master-index and template-index.
- Upgraded dashboard builder to emit static HTML.
- Added template confusion matrix and test harness.
- Removed `__pycache__` from distribution packaging.
