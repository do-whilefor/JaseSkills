---
name: 01-authorized-maximum-orchestrator
description: 最高入口：授权边界、任务分发、技能路由、质量门槛、证据清单、动态验证闭环
---

# 01-authorized-maximum-orchestrator

最高入口：授权边界、任务分发、技能路由、质量门槛、证据清单、动态验证闭环

## 原始来源映射

本 skill 合并/承接 22 个原始 `SKILL.md` 的相关能力。代表来源：

- `Eyadkelleh-awesome-claude-skills-security/awesome-claude-skills-security-86d2316b278ac266b5407a7b23d0b8c294dd0e54/seclists-categories pattern-matching/pattern-matching/SKILL.md`
- `MyuriKanao-src-hunter-skill/src-hunter-skill-978b95318163656c5d2d9902dbe6c5ea54c7e800/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/bb-methodology/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/bug-bounty/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/report-writing/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/triage-validation/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-ai-tools/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-hunt-foundation/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-methodology-research/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-triage-report/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/building-secure-contracts/skills/algorand-vulnerability-scanner/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/building-secure-contracts/skills/solana-vulnerability-scanner/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/property-based-testing/skills/property-based-testing/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/genotoxic/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/coordination/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/essential-tools/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/hackerone/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/skill-prune/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/ti-ingest/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/orchestration/supabase-help/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/orchestration/supabase-pentest/SKILL.md`

## 触发条件

用户要求对授权项目进行安全审计、skills 合并后审计、漏洞挖掘、动态验证、报告生成、回归测试或证据质量审查时触发。

## 执行步骤

1. 读取授权范围，建立任务 ID 和证据目录。
2. 调用 02 识别项目；调用 03 构建代码图谱；调用 04 建暴露面。
3. 若存在前端/JS/bundle/source map，调用 05。
4. 对候选调用 07；需要动态证据时调用 06。
5. 所有候选进入 08 评分，只有达标才交给 09。
6. 调用 10 做回放和 dashboard。

## 特殊规则

任何原始 skill 的能力未能映射时，必须标记为 `lost_capability_risk`，不得宣称合并完成。

## 授权和禁止条件

仅处理用户明确授权的项目、用户提供的代码、日志、请求/响应、HAR、Burp/Playwright/MCP 证据、知识库和测试样本。禁止第三方非授权目标、MITM、DoS、大规模压测、凭证喷洒、社工、持久化后门、删除/篡改真实数据、破坏性验证。

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
