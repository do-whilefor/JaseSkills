# v2 攻击性审计报告

## 审计结论

上一版 `seckb-claude-skills-complete` 具备基本结构，但属于“框架完整、硬约束不足”的版本。主要问题不是缺少目录，而是缺少可执行仲裁层、缺少能力指纹、缺少失败案例库、缺少不可交付字段、缺少维护者变更规则、缺少自测脚本对 SKILL.md 的结构化检查。

## 最严重的 20 个问题与修复

| # | 缺陷 | 影响 | 修复 |
|---:|---|---|---|
| 1 | 总控 Skill 有路由意图，但缺少任务分类评分 | 模糊任务可能直奔子 Skill | 在 01 增加 `任务分类器` 和 `路由仲裁表` |
| 2 | 缺少全局能力索引 | 不熟悉文档的 Claude 需要逐个 Skill 猜用途 | 新增 `CAPABILITY_INDEX.md` |
| 3 | 文档映射矩阵太粗 | 无法证明每个关键句被保留 | 新增 `document-fingerprint-matrix.md` 和 `mirror-mapping-matrix.md` |
| 4 | 质量门禁只在脚本中简化体现 | Claude 可能绕过门禁直接输出结论 | 新增 `docs/quality-gate-policy.md`，并强化 `quality_gate.py` |
| 5 | 缺少失败案例库 | Claude 容易重复误报 | 新增 `examples/failure-case-library.md` |
| 6 | 缺少不可交付原因 | 证据不足时可能硬交付 | 新增 `templates/non-deliverable-reasons.md` |
| 7 | RAG 测试只有示例，不做断言 | 无法自动发现误路由 | 强化 `scripts/rag_route_tests.py` 输出 expected/forbidden/stop_condition |
| 8 | 反幻觉规则分散在各 Skill | 运行时可能遗漏 | 新增 `docs/anti-hallucination-policy.md` 并在 README 引用 |
| 9 | 没有维护者说明 | 后续修改可能破坏原始能力 | 新增 `docs/maintenance-guide.md` |
| 10 | 没有版本变更记录 | 无法追踪能力变化 | 新增 `docs/version-changelog.md` |
| 11 | 缺少“最小/标准/专家”三档路径 | 输出容易过长或过浅 | 每个 SKILL.md 追加 v2 执行档位 |
| 12 | 缺少输出熵控制 | Claude 可能堆砌概念 | 新增默认五段输出：结论/依据/映射/缺口/下一步 |
| 13 | 目录结构与 SecKB 目标目录之间有一层 Skills 包差异 | 新手可能把 Skills 目录当 SecKB 目录 | README 增加 Skills 目录与 SecKB 目录分离说明 |
| 14 | sample-records 使用 placeholder | 容易被当成真实记录 | 改为显式 `example_only=true`，禁止 promoted |
| 15 | update_sources.ps1 过于空泛 | 可能被误解为真实联网采集器 | 增加“清单生成器/导入器”说明，不声称抓取能力 |
| 16 | `record.schema.json` required 字段少于原文最小字段 | 可能让缺字段记录通过 | 强化 required 列表接近原文完整字段 |
| 17 | 没有检查 SKILL.md 结构完整性 | Skill 可能缺触发、禁止、输入、输出 | 新增 `scripts/self_audit_skills.py` |
| 18 | 没有压缩包冒烟测试 | 打包后可能缺文件 | 新增 `scripts/smoke_test_package.py` |
| 19 | 延伸内容标注不够集中 | Claude 可能误以为都是原文 | 新增 `docs/extension-register.md` |
| 20 | 没有缺席测试 | 无法判断 Skill 是否冗余 | 新增 `examples/absence-tests.md` |

## 文档保真度缺陷清单

1. 原文要求的 SRC 规则 18 个字段在 06 中保留，但模板中字段表达偏简，已在 `templates/src-rule-template.md` 扩展。
2. 原文要求漏洞模板 25 个字段，上一版模板覆盖但不够强制，已在 `templates/vuln-template.md` 和 `record.schema.json` 增加强制字段。
3. 原文要求“先读索引再读细节”，上一版写入 01/03，但没有全局索引入口，已新增 `CAPABILITY_INDEX.md`。
4. 原文要求“本次联网学习输出 15 项”，上一版未形成专用输出模板，已新增 `templates/learning-run-summary.md`。
5. 原文要求“反向审计输出 18 项”，上一版分散在 10 中，已新增 `templates/audit-run-summary.md`。
6. 原文要求“失败复现墓地、负证据账本、漏洞谱系图”等偏门方法，上一版只在 09/10 描述，已新增对应模板。
7. 原文要求“宁可 needs_review”，上一版规则存在但脚本门禁不足，已强化 `quality_gate.py`。
8. 原文要求“任何 SRC 规则必须官方页面为准”，上一版没有独立官方性判定模板，已新增 `templates/source-confidence-rubric.md`。

## 触发稳定性缺陷清单

- 模糊任务可能绕过 01：修复为“任何 SecKB 相关任务必须先经 01”。
- 02 与 07 可能争抢工具 release 任务：修复为 02 采集来源，07 解读工具能力。
- 04 与 09 可能争抢 patch diff：修复为 09 抽根因，04 生成模板。
- 06 与 08 可能争抢可报告性判断：修复为 06 判断边界，08 判断证据闭环。
- 10 与所有 Skill 都有审计重叠：修复为 10 只做二次审计，不做原始采集或验证。

## 执行闭环缺陷清单

上一版每个 Skill 有步骤，但缺少“最短路径”和“专家路径”。v2 为每个 Skill 追加三档执行路径：

- 最小执行：只输出能安全推进的一步。
- 标准执行：完成输入、处理、输出、质量门禁。
- 专家执行：附加映射矩阵、负样本、冲突检测、维护建议。

## 仍然不能解决的问题

1. 本包无法保证实际联网采集结果质量，因为需要运行环境具备网络和对应访问权限。
2. 本包无法替代人工确认 SRC 当前规则，因为规则页面可能随时变化。
3. 本包无法证明某个漏洞真实存在，除非在授权环境内执行动态验证并保存证据。
4. 本包无法保证 Claude Runtime 一定以预期方式调度 Skills，只能通过触发规则和测试样例提高稳定性。
