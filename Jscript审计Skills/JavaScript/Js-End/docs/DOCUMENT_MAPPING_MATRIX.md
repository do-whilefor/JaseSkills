# 文档到 Skill 映射矩阵

| 原文能力指纹 | 必须保留字段 | Skill | 输出产物 | 质量门槛 |
|---|---|---|---|---|
| “递归分析项目目录结构” | 路径、类型、作用、暴露面、风险、优先级 | 02 | 代码目录知识图谱 | 不得只列目录 |
| “从代码真实调用链解释应用如何运行” | 启动、请求、路由、中间件、鉴权、数据流、状态 | 02 | 运行流程图/信任边界 | 入口不确定必须标记 |
| “自动提取所有输入源” | 参数名、来源、文件、函数、传播、sink、校验、权限 | 03 | 参数表 | 无 source/sink 不定漏洞 |
| “路由→控制器→服务→DAO→sink” | 调用链、sink、鉴权、权限矩阵 | 03 | source-to-sink 图谱 | 候选必须交 07 |
| “配置风险表” | 当前值、安全影响、触发路径、验证方法、修复建议 | 04 | 配置风险表 | 不得编造环境 |
| “依赖风险不要只报 CVE” | 版本、使用位置、可达性、实际链路、不可报告原因 | 04 | 依赖风险表 | 不可达必须剔除 |
| “高危 JS 漏洞重点挖掘” | 23 类漏洞、优先级、验证方法 | 06 | 候选列表 | 不能 verified |
| “前端 JS 深挖” | API、权限、storage、签名、DOM sink | 05 | 前端暴露面表 | 需反哺后端验证 |
| “每个候选 18 字段验证计划” | 代码证据、入口、链路、反证、三次复现、不可提交原因 | 06/07 | 验证计划 | 缺字段不可交付 |
| “每个最终漏洞证据标准” | 代码、请求、响应、三次复现、反证、影响 | 08 | manifest/QG | 缺一项降级 |
| “动态验证 22 字段模板” | 22 字段 | 07/templates | 单漏洞验证记录 | 三次复现强制 |
| “证据 manifest” | JSON 字段 | 08/schema | manifest | schema + gate 双校验 |
| “覆盖率反思 50 项” | 已覆盖/未覆盖/覆盖不足 | 09 | 覆盖率表 | 未覆盖必须给补测路径 |
| “小众路径 30 项” | 假设、代码位置、验证、反证 | 09 | 新增假设 | 不得写成漏洞 |
| “误报审查” | 保留/降级/删除/证据不足/不可报告 | 09 | 修正列表 | 缺证据必须降级 |

| 粘贴文本：十五部分最终输出格式 | templates/extreme-skills-review-report.md | 逐节模板化 |
| 粘贴文本：JS 收集点 | data/js_collection_points.json | 逐项矩阵化 |
| 粘贴文本：JS 审计能力 | data/js_audit_capabilities.json | 逐项矩阵化 |
| 粘贴文本：严重 JS 漏洞链 | data/js_severe_vulnerability_chains.json | 逐项矩阵化 |
| 粘贴文本：脚本工程落地评审 | data/script_inventory_expected.json | 逐项矩阵化 |
| 粘贴文本：硬性证据要求 | 12-js-skills-extreme-reviewer/SKILL.md, schemas/extreme-review.schema.json | 状态和证据字段化 |


## 第二轮反向审查映射

| 用户要求 | 承载文件 | 验收方式 |
| --- | --- | --- |
| 逐条反查原评估结论 | `data/second_pass_original_conclusion_checks.json`、`scripts/second_pass_reverse_audit.py` | `tests/last-second-pass-review.md` 第一部分 |
| 30 个 JS 收集点反查 | `data/second_pass_js_collection_points.json` | 第二部分表格必须 30 行 |
| 20 个 JS 审计能力反查 | `data/second_pass_js_audit_capabilities.json` | 第三部分表格必须 20 行 |
| 25 个严重 JS 漏洞链反查 | `data/second_pass_severe_js_chains.json` | 第四部分表格必须 25 行 |
| 文件级覆盖率 | `scripts/second_pass_reverse_audit.py` | 第五部分列出核心目录和所有文件 |
| 评分虚高反查 | `data/second_pass_score_rules.json` | 第六部分输出原分与修正分 |
| P0/P1/P2 可执行性 | `templates/second-pass-reverse-audit-report.md` | 第七部分包含命令、验收、回滚 |
| 40 个偏门点 | `data/second_pass_unconventional_js_audit_points.json` | 第八部分表格必须 40 行 |


| 终极反向审判 / 证据法庭要求 | `14-js-skills-evidence-court/SKILL.md`、`scripts/final_evidence_court_audit.py`、`data/final_court_*.json`、`templates/final-evidence-court-report.md`、`schemas/final-evidence-court.schema.json` | 输出前两轮结论审判、20 起 JS 收集漏报事故、10 类伪能力、30 类严重漏洞漏报、工程验尸、失败惩罚评分、不可辩解 P0 |


| 用户要求：把 JS 收集、JS 分析、JS 审计做到顶级 | `15-js-top-tier-collection-analysis-audit/SKILL.md` | `scripts/js_top_tier_collect.py`, `scripts/js_top_tier_analyze.py`, `scripts/js_runtime_evidence_bridge.py`, `scripts/js_role_tenant_diff.py`, `scripts/js_top_tier_quality_gate.py` | `schemas/js-top-tier-ledger.schema.json`, `schemas/js-top-tier-finding.schema.json` | `templates/js-top-tier-report.md` |
