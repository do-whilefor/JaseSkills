---
name: 09-reporting-disclosure
description: 漏洞报告、复现步骤、影响分析、修复建议、证据附件、风险等级、CVSS 初评
---

# 09-reporting-disclosure

漏洞报告、复现步骤、影响分析、修复建议、证据附件、风险等级、CVSS 初评

## 原始来源映射

本 skill 合并/承接 15 个原始 `SKILL.md` 的相关能力。代表来源：

- `MyuriKanao-src-hunter-skill/src-hunter-skill-978b95318163656c5d2d9902dbe6c5ea54c7e800/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/bug-bounty/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/report-writing/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/triage-validation/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-triage-report/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/entry-point-analyzer/skills/entry-point-analyzer/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/trailmark-structural/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/formats/transilience-report-style/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/cve-poc-generator/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/essential-tools/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/hackerone/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/web-app-logic/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/report/supabase-report/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/report/supabase-report-compare/SKILL.md`

## 触发条件

候选已通过质量门槛，需要生成漏洞报告、复现步骤、影响分析、修复建议、附件索引和 CVSS 初评时触发。

## 执行步骤

1. 只引用 evidence manifest 中 `confirmed` 或明确标注 `needs_review` 的候选。
2. 报告必须包含复现环境、权限前提、边界、证据、负样本、修复位置。
3. 不夸大影响；不能把未验证假设写成事实。
4. 输出 `reports/<candidate_id>.md` 和 `report_index.json`。

## 授权和禁止条件

仅处理用户明确授权的本机项目、用户提供的代码、日志、请求/响应、HAR、Burp/Playwright/MCP 证据、知识库和测试样本。禁止第三方非授权目标、MITM、DoS、大规模压测、凭证喷洒、社工、持久化后门、删除/篡改真实数据、破坏性验证。

## 输入要求

- 项目路径或已上传源码/压缩包。
- 授权范围、禁止范围、环境说明。
- 可选：运行方式、账号角色、租户/组织、Burp/Playwright/HAR/日志、现有候选漏洞。

## 输出要求

输出必须包含来源文件、行号或证据路径、判断依据、失败/缺失项、下一跳交接对象。漏洞类输出必须写入 evidence manifest 或明确说明为何不能写入。

## 失败处理

工具不可用时记录 `tool_unavailable`，切换到静态/手工证据路径，状态不得高于 `needs_review`。输入不足时先产出可确认的资产/缺口，不编造事实。

## 质量门槛

遵守根目录 `QUALITY_GATE.md`。不得把工具告警、异常、前端暴露或单次请求直接确认为漏洞。

## 测试样例

使用 `REGRESSION_TEST_PLAN.md` 中相关用例回放；每个 skill 至少覆盖正样本、负样本、模糊路由和工具不可用降级。

## 交接协议

交接对象必须接收结构化 JSON 或 markdown 表：`task_id`、`scope`、`inputs`、`outputs`、`evidence_refs`、`missing_evidence`、`next_skill`、`status`。


## 机器可校验交接契约

输入、输出和下一跳必须遵守 `config/core_skill_routing.json`。缺字段写入 `missing_evidence`，不得隐式补全。工具不可用必须引用 `outputs/tool_availability.json`，候选最高 `needs_review`。
