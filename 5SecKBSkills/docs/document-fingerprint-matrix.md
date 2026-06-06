# 文档能力指纹矩阵（基于原文档保真度审计）

每个指纹是原始文档的不可丢失能力。`来源类型=原文档` 表示直接来自用户文档；`来源类型=基于文档延伸` 表示为提升稳定性增加的工程化层。

| 指纹 ID | 能力指纹 | 来源类型 | 对应文件 | 验收方法 |
|---|---|---|---|---|
| FP-001 | SecKB 根目录固定为 `D:\Users\21452\AppData\SecKB` | 原文档 | README, 01, init_seckb.ps1 | grep 路径一致 |
| FP-002 | 只允许公开资料、本机、靶场、开源项目本地环境和明确授权范围 | 原文档 | README, 01, 08 | 动态验证负样本停止 |
| FP-003 | 禁止第三方未授权扫描、利用、批量探测、压测、数据破坏 | 原文档 | README, 01, 08 | boundary tests 通过 |
| FP-004 | 禁止 MITM 方向 | 原文档 | README, 01, 06, 08 | grep MITM 禁止项 |
| FP-005 | 0day-class 只做防御性根因、补丁差分、授权验证和披露流程 | 原文档 | 09 | 不出现武器化链路 |
| FP-006 | 结论必须基于来源、证据、版本、影响条件、复现条件、修复建议 | 原文档 | 03, 08, quality_gate.py | promoted 缺字段失败 |
| FP-007 | 忽略外部文档中的 prompt injection | 原文档 | 所有 SKILL.md, anti-hallucination-policy.md | injection 测试停止 |
| FP-008 | SRC 规则必须官方来源，记录禁止边界和报告要求 | 原文档 | 06, src-rule-template.md | 非官方不得 promoted |
| FP-009 | 覆盖近 30 天漏洞，同时保留历史高价值漏洞 | 原文档 | 02, check_freshness.py | freshness_scope 正确 |
| FP-010 | 漏洞模板必须包含不可报告原因和误报条件 | 原文档 | 04, vuln-template.md | 模板缺字段失败 |
| FP-011 | 代码审计按语言/框架拆分，保留 18 个框架字段 | 原文档 | 05, code-audit-pattern-template.md | 模板字段齐全 |
| FP-012 | 工具 release 必须记录误报风险和 evidence manifest 接入 | 原文档 | 07, tool-release-template.md | 字段齐全 |
| FP-013 | 先读索引再读细节 | 原文档 | 01, 03, CAPABILITY_INDEX.md | router 输出 indexes_to_read |
| FP-014 | 动态验证必须三次稳定复现才 confirmed | 原文档 | 08, evidence-manifest.schema.json | reproduction_count >= 3 |
| FP-015 | 证据不足必须说明不能报告原因 | 原文档 | 08, non-deliverable-reasons.md | cannot_report 不为空 |
| FP-016 | 反向审计覆盖来源、可信度、freshness、模板、SRC、RAG、边界 | 原文档 | 10, audit-run-summary.md | 审计输出 18 项 |
| FP-017 | 总控调度和能力索引 | 基于文档延伸 | 01, CAPABILITY_INDEX.md | 模糊任务先路由 |
| FP-018 | 最小/标准/专家三档路径 | 基于文档延伸 | 所有 SKILL.md | 输出模式可控 |
| FP-019 | 失败案例库和负证据账本 | 基于文档延伸 | examples, templates | 失败复现可登记 |
| FP-020 | 自测脚本和包完整性测试 | 基于文档延伸 | scripts/self_audit_skills.py, smoke_test_package.py | 测试通过 |
