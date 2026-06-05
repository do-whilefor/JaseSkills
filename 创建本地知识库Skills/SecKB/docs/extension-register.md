# 延伸内容登记

以下内容不是原文档逐字要求，而是为了让 Skills 更稳定执行而增加，均属于**基于文档延伸**。

| 延伸项 | 原因 | 风险控制 |
|---|---|---|
| CAPABILITY_INDEX.md | 降低触发混乱 | 不改变原文档能力，只做路由索引 |
| 最小/标准/专家三档路径 | 控制输出长度和深度 | 默认最小或标准，不强制长报告 |
| self_audit_skills.py | 自动检查 SKILL.md 结构完整性 | 只检查文本结构，不伪造结论 |
| smoke_test_package.py | 检查包文件完整性 | 只做本地文件检查 |
| failure-case-library.md | 让 Claude 学会不能报告的场景 | 不包含攻击性步骤 |
| negative-evidence-ledger.md | 沉淀失败复现和不可报告原因 | 防止误报升级 |
| quality-gate-policy.md | 把门槛集中化 | 与原文 promoted 条件保持一致 |
| anti-hallucination-policy.md | 集中反幻觉规则 | 不覆盖系统规则，只约束本 Skills |

## v3 延伸登记

1. `claude_code_replay.py`：基于文档“RAG 路由反思”和负样本测试要求延伸，用于 Claude Code 触发回放。
2. `records_100.json/jsonl`：基于文档“quality_gate.py”和 review 状态要求延伸，用于质量门禁压测。
3. `check_index_consistency.py`：基于文档“先读索引再读细节”和索引要求延伸，用于检查索引与记录一致性。
4. `dashboard_build.py --format html`：基于文档“dashboard 轻量设计”和输出要求延伸，使用静态 HTML，避免外部依赖。
5. `template-confusion-matrix`：基于文档“模板混淆矩阵”和模板误用审计要求延伸。
