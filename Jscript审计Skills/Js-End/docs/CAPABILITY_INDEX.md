# 能力索引

| 能力 | 来源 | Skill | 状态 |
|---|---|---|---|
| 目录结构与语言识别 | 原文静态审计阶段 1 | 02 | 原文保留 |
| 工作原理剖析 | 原文静态审计阶段 2 | 02 | 原文保留 |
| 参数与输入面检查 | 原文静态审计阶段 3 | 03 | 原文保留 |
| 代码知识图谱 | 原文静态审计阶段 4 | 03 | 原文保留 |
| 配置文件分析 | 原文静态审计阶段 5 | 04 | 原文保留 |
| 依赖与供应链分析 | 原文静态审计阶段 6 | 04 | 原文保留 |
| 框架级漏洞挖掘 | 原文静态审计阶段 7 | 04/06 | 原文保留 |
| 高危 JS 漏洞重点挖掘 | 原文静态审计阶段 8 | 06 | 原文保留 |
| 前端 JS 深挖 | 原文静态审计阶段 9 | 05 | 原文保留 |
| 动态验证计划 | 原文静态审计阶段 10 | 06/07 | 原文保留 |
| 证据标准 | 原文静态审计阶段 11 | 01/08 | 原文保留 |
| 最终输出格式 | 原文静态审计阶段 12 | 10 | 原文保留 |
| 环境确认 | 原文动态验证阶段 1 | 07 | 原文保留 |
| 候选归档 | 原文动态验证阶段 2 | 07 | 原文保留 |
| 优先级排序 | 原文动态验证阶段 3 | 06/07 | 原文保留 |
| 单漏洞 22 字段模板 | 原文动态验证阶段 4 | 07/templates | 原文保留 |
| 动态验证方式 | 原文动态验证阶段 5 | 07 | 原文保留 |
| 三次复现 | 原文动态验证阶段 7 | 07/08 | 原文保留 |
| 反证要求 | 原文动态验证阶段 8 | 07/08 | 原文保留 |
| 证据 manifest | 原文动态验证阶段 9 | 08/schema | 原文保留 |
| 覆盖率反思 50 项 | 原文反向审查部分 1 | 09/tests | 原文保留 |
| 小众路径 30 项 | 原文反向审查部分 2 | 09 | 原文保留 |
| 高危链式重组 18 项 | 原文反向审查部分 3 | 09 | 原文保留 |
| 误报审查 | 原文反向审查部分 4 | 09 | 原文保留 |
| 动态验证质量审计 | 原文反向审查部分 5 | 09 | 原文保留 |
| 至少 20 个深挖假设 | 原文反向审查部分 6 | 09 | 原文保留 |
| 小程序/Electron/Extension 专项 | 原文场景覆盖 + 文档延伸 | 11 | 延伸隔离 |
| 自动化脚本与自测 | 工程落地延伸 | scripts/tests | 延伸隔离 |

| Skills 包极限评审 | 用户粘贴的评审要求 | 12 | 新增可执行评审入口 |
| JS 收集能力矩阵 | 用户粘贴的 JS 收集 20 项 | 12/data | 新增保守评审清单 |
| JS AST/语义审计矩阵 | 用户粘贴的 JS 审计 32+ 项 | 12/data | 新增保守评审清单 |
| 严重 JS 漏洞链矩阵 | 用户粘贴的 30 类严重链 | 12/data | 新增保守评审清单 |
| 信息收集与 JS 联动矩阵 | 用户粘贴的联动 15 项 | 12/data | 新增保守评审清单 |
| 自动极限评审脚本 | 工程落地延伸 | scripts/extreme_skills_review.py | 新增，不伪装 runtime ready |
| 极限评审报告模板 | 用户粘贴最终输出格式 | templates/extreme-skills-review-report.md | 新增 |


| 第二轮反向审查 | 用户二次反审要求 | 13 | 新增，强制检查文件证据/测试证据/评分虚高 |
| 原评估结论逐条反查 | 二次反审第 1 部分 | 13/data/scripts | 新增，缺证据则降级 |
| 30 个 JS 收集点反查 | 二次反审第 2 部分 | 13/data | 新增，区分 doc-only 与真实 collector |
| 20 个 JS 审计保真反查 | 二次反审第 3 部分 | 13/data | 新增，防止关键词误判语义审计 |
| 25 个严重 JS 漏洞链反查 | 二次反审第 4 部分 | 13/data | 新增，检查 detector/dynamic/template |
| 文件级覆盖率反查 | 二次反审第 5 部分 | 13/scripts | 新增，列出目录和文件覆盖 |
| 评分虚高反查 | 二次反审第 6 部分 | 13/data | 新增，文档不计实现分 |
| P0/P1/P2 可执行性反查 | 二次反审第 7 部分 | 13/templates | 新增，包含命令/验收/回滚/保真 |
| 40 个偏门 JS 审计点 | 二次反审第 8 部分 | 13/data | 新增，进入 needs_review 流程 |
## 14-js-skills-evidence-court

- 类型：终极反向审判 / 证据法庭 / 失职追责。
- 输入：前两轮评估输出、`data/final_court_*.json`、当前文件树。
- 输出：`tests/last-final-evidence-court.json`、`tests/last-final-evidence-court.md`。
- 严格状态：本 Skill 默认降级无 runtime evidence 的能力，禁止把 doc-only / candidate-only 写成 ready。
- 仍未实现的真实能力：AST backend、Source Map parser、Playwright/Burp/HAR bridge、role/tenant replay、detector registry、schema validator、report generator、dashboard generator、真实 OSS replay。



## 15-js-top-tier-collection-analysis-audit

| 能力 | 承载文件 | 当前状态 | 证据输出 |
| --- | --- | --- | --- |
| HTML/manifest/chunk/source map/worker/WASM/HAR 收集 | `scripts/js_top_tier_collect.py` | implemented-offline / partial | `reports/js-top-tier/js_asset_ledger.json` |
| JS AST backend 适配 | `scripts/backends/js/babel_extract.mjs`, `scripts/backends/js/typescript_extract.mjs` | runtime-dependent | `js_analysis.json.backend_status` |
| JS source/sink/auth/tenant 候选审计 | `scripts/js_top_tier_analyze.py` | candidate-only unless AST backend ready | `js_findings.json` |
| Runtime evidence bridge | `scripts/js_runtime_evidence_bridge.py` | HAR/trace/screenshot bridge | `js_runtime_evidence.json` |
| Role/tenant diff | `scripts/js_role_tenant_diff.py` | requires multiple ledgers | `js_role_tenant_diff.json` |
| 质量门槛 | `scripts/js_top_tier_quality_gate.py` | executable | `js_quality_gate.json` |
| 报告/dashboard 闭环 | `scripts/js_top_tier_report_generator.py` | executable | `js_top_tier_report.md`, `js_top_tier_dashboard.html` |
