# 12 JS Skills Extreme Reviewer

## 职责边界

这是针对“JS 安全审计 Claude Skills 包本身”的极限评审 Skill。它不审计业务目标站点，不直接挖真实漏洞，而是审查一个 Skills 包是否具备顶级 JS 收集、JS 审计、严重 JS 漏洞发现、动态验证、证据沉淀、报告输出、质量门槛、自检回放能力。

必须把文档声明、脚本实现、schema、模板、tests、fixtures、knowledge、dashboard 和实际可执行链路逐一对照。发现没有文件证据的能力，一律标为 `未证实`、`doc-only`、`missing` 或 `fake-ready`，不得写成已实现。

## 必须触发

用户要求评审、反向审查、打分、修复、压缩包清理、skills 包结构审查、JS 收集能力评审、JS 审计能力评审、严重 JS 漏洞发现能力评审、动态验证能力评审、证据链审查、quality gate 审查、replay 审查、知识库/漏洞模板保真度审查时触发。

高置信触发词：`skills 评审`、`顶级 JS 审计 skills`、`JS 收集评审`、`JS 审计评审`、`严重 JS 漏洞发现`、`动态验证`、`证据 manifest`、`quality gate`、`replay`、`dashboard`、`fake-ready`、`doc-only`、`parser backend`、`Playwright/Burp/HAR`、`多角色/多租户`、`压缩包修复`。

## 禁止触发

普通业务项目代码审计、普通前端漏洞挖掘、真实目标动态验证、未授权公网测试、破坏性测试、绕过安全保护、数据窃取、凭据外带、DoS、爆破、恶意 payload 生成。遇到这些请求必须回到 01 授权门禁或给出安全替代。

## 输入

- Skills 包目录或 zip。
- 用户粘贴的评审要求。
- 当前包内目录树、SKILL.md、README、CLAUDE.md、docs、scripts、tools、bin、lib、src、tests、fixtures、schemas、templates、knowledge、reports、dashboard。
- 自检命令输出，例如 `python scripts/package_self_check.py .`、`python scripts/extreme_skills_review.py . --markdown out.md`。

## 输出

必须输出 15 个固定部分：

1. 执行摘要。
2. Skills 包结构审查。
3. JS 收集能力审查。
4. JS 审计能力审查。
5. 严重 JS 漏洞发现能力审查。
6. 信息收集与 JS 联动审查。
7. 脚本工程落地审查。
8. Markdown 文件一致性审查。
9. 知识库与漏洞模板保真度审查。
10. 动态验证与证据链审查。
11. 测试与 replay 审查。
12. 质量评分。
13. P0/P1/P2 修复清单。
14. 顶级标准差距。
15. 最终结论：当前分数、目标分数、最短补强路径。

## 状态词典

JS 收集能力真实程度只能使用：

| 状态 | 判定标准 |
|---|---|
| ready | 有可执行实现、真实调用链、测试样本、证据输出；依赖可用性有检查。 |
| partial | 有部分脚本或规则，但覆盖不完整、调用链不全或测试不足。 |
| doc-only | 只有 Markdown/模板/说明，没有可执行实现。 |
| fake-ready | 声明 ready，但缺运行依赖、脚本不可执行、没有 runtime check、没有测试或自相矛盾。 |
| missing | 没有文档、脚本、模板、测试、schema 证据。 |
| conflict | 多个规则、模板、schema 或脚本互相冲突。 |

## 执行步骤

1. 解包并生成目录树摘要；记录所有文件路径，不得凭印象判断。
2. 检查每个二级 Skill 是否有 `SKILL.md`，并检查是否包含触发条件、禁止条件、输入、输出、执行步骤、工具依赖、证据要求、失败处理、质量门槛、交接规则。
3. 检查冗余：`__pycache__`、`.pyc`、临时文件、缓存文件、重复 zip、构建产物、空目录、过期报告。
4. 用 `data/js_collection_points.json` 审查 JS 收集能力；逐项给出状态、对应文件、缺陷、漏洞挖掘影响、修复方式、测试样本。
5. 用 `data/js_audit_capabilities.json` 审查 AST/语义审计能力；严禁把 grep/regex/keyword 当成 AST/CFG/DFG/source-sink。
6. 用 `data/js_severe_vulnerability_chains.json` 审查 30 类严重 JS 漏洞链；没有动态验证和多角色/多租户证据时，不得给高分。
7. 用 `data/info_js_linkage_matrix.json` 检查信息收集与 JS 审计闭环：子域、URL crawl、截图、登录态、多角色、多租户、HAR、Burp sitemap、Playwright trace、报告模板。
8. 检查脚本清单：route_extractor、js_asset_extractor、sourcemap_parser、endpoint_extractor、knowledge_graph_builder、evidence_manifest_generator、quality_gate、dashboard_generator、selftest、replay harness、AST parser backend、Playwright/Burp/HAR bridge、report generator、template index checker、knowledge index checker。
9. 检查所有 Markdown：声明能力是否有脚本、schema、测试、fixtures 支撑；是否存在计划写成 ready、过期引用、遗漏授权边界、遗漏失败处理、遗漏 human review。
10. 检查 knowledge/template 保真度：知识库是否有索引、触发条件、冲突处理、引用路径；漏洞模板是否与 evidence manifest、quality gate、report section 绑定。
11. 给出 100 分严格评分，不允许虚高。无真实 parser backend、无 runtime browser bridge、无多角色 replay、无正/负/阻断样本时必须扣分。
12. 输出 P0/P1/P2 工程修复清单，每项包含编号、问题、影响、修改文件、新增文件、测试、验收标准、回滚方案。
13. 最后运行或要求运行 `scripts/extreme_skills_review.py` 与 `scripts/package_self_check.py`，把命令输出作为证据；未运行则标记“未执行”。

## 必填表格

### Skills 包结构审查

| 文件/目录 | 当前作用 | 发现问题 | 安全影响 | 工程影响 | 修复建议 | 优先级 |
|---|---|---|---|---|---|---|

### JS 收集能力评审

| JS 收集点 | 当前是否支持 | 对应文件 | 真实程度 | 缺陷 | 漏洞挖掘影响 | 修复方式 | 测试样本 |
|---|---|---|---|---|---|---|---|

### JS 审计能力评审

| 审计能力 | 当前实现文件 | 方法类型 | 是否语义级 | 缺陷 | 会漏掉什么严重漏洞 | 修复方案 | 应增加的测试 |
|---|---|---|---|---|---|---|---|

### 严重 JS 漏洞发现能力评审

| 漏洞链 | Skills 是否覆盖 | 证据来源 | 当前检测深度 | 是否支持动态验证 | 是否支持多角色/多租户 | 漏报风险 | 误报风险 | 修复建议 |
|---|---|---|---|---|---|---|---|---|

### 信息收集与 JS 联动评审

| 联动链路 | 当前是否闭环 | 对应文件 | 断点 | 影响 | 修复方式 |
|---|---|---|---|---|---|

### 脚本与工程落地评审

| 脚本 | 输入 | 输出 | 是否可执行 | 是否有测试 | 是否真实调用 | 是否处理失败 | 是否产生证据 | 主要缺陷 | 修复建议 |
|---|---|---|---|---|---|---|---|---|---|

### Markdown 文件评审

| Markdown 文件 | 声明能力 | 实际支撑文件 | 不一致点 | 风险 | 修复建议 |
|---|---|---|---|---|---|

### 质量评分

| 评分项 | 分数 | 扣分原因 | 证据文件 | 提升到顶级所需修复 |
|---|---:|---|---|---|

### P0/P1/P2 修复清单

| 优先级 | 编号 | 问题 | 修改文件 | 新增文件 | 测试 | 验收标准 |
|---|---|---|---|---|---|---|

## 评分规则

| 评分项 | 满分 | 严格扣分原则 |
|---|---:|---|
| Skills 包结构 | 10 | 缺 SKILL.md、路由冲突、空壳 Skill、冗余缓存、模板未绑定扣分。 |
| 信息收集能力 | 10 | 无子域/URL/HAR/Burp/Playwright 联动扣分。 |
| JS 收集能力 | 15 | 无 chunk/source map/runtime asset ledger/失败处理扣分。 |
| JS AST / 语义审计能力 | 20 | 无 Babel/TS Compiler API/tree-sitter/CFG/DFG/source-sink/auth tenant-aware detector 大幅扣分。 |
| 严重 JS 漏洞发现能力 | 20 | 只有候选规则、无动态验证、无多角色多租户 replay、无严重链模板扣分。 |
| 动态验证与证据链 | 10 | 无真实请求/响应/HAR/截图/三次复现/反证/evidence manifest 扣分。 |
| 测试与回放 | 10 | 无正样本、负样本、阻断样本、needs_review、真实 OSS replay 扣分。 |
| 知识库与模板保真度 | 5 | 知识库无索引、模板未绑定 quality gate/report 扣分。 |

## 硬性证据要求

每个结论至少绑定一种证据：文件路径、脚本名、函数名、schema 字段、模板名、测试用例名、fixture 名、dashboard 字段、manifest 字段、命令输出。没有证据必须标记为“未证实”。

## 交接

- 发现包结构或路由问题：交给 00、docs/ROUTING_TABLE.md、scripts/skill_dispatcher.py。
- 发现证据/质量门槛问题：交给 08、schemas、templates、scripts/strict_quality_gate.py。
- 发现 JS 收集/审计能力文档化但未实现：交给 05、06、data/checklists、scripts/extreme_skills_review.py。
- 发现动态验证问题：交给 07、fixtures、templates、evidence manifest。
- 需要最终报告：交给 10 与 `templates/extreme-skills-review-report.md`。
