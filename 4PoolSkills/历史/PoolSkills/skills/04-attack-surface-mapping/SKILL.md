---
name: 04-attack-surface-mapping
description: HTTP/API/GraphQL/WebSocket/RPC/gRPC/CLI/任务/上传下载/模板/URL fetch/权限边界暴露面
---

# 04-attack-surface-mapping

HTTP/API/GraphQL/WebSocket/RPC/gRPC/CLI/任务/上传下载/模板/URL fetch/权限边界暴露面

## 原始来源映射

本 skill 合并/承接 38 个原始 `SKILL.md` 的相关能力。代表来源：

- `MyuriKanao-src-hunter-skill/src-hunter-skill-978b95318163656c5d2d9902dbe6c5ea54c7e800/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/bug-bounty/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/security-arsenal/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/web2-recon/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/web2-vuln-classes/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/trailmark/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/trailmark-structural/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/api-security/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/client-side/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/reconnaissance/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/server-side/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/web-app-logic/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-api/supabase-audit-rls/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-api/supabase-audit-rpc/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-api/supabase-audit-tables-list/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-api/supabase-audit-tables-read/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-auth/supabase-audit-auth-config/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-auth/supabase-audit-auth-signup/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-auth/supabase-audit-auth-users/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-auth/supabase-audit-authenticated/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-functions/supabase-audit-functions/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-realtime/supabase-audit-realtime/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-storage/supabase-audit-buckets-list/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-storage/supabase-audit-buckets-public/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/audit-storage/supabase-audit-buckets-read/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/detection/supabase-detect/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/evidence/supabase-evidence/SKILL.md`
- `yoanbernabeu-supabase-pentest-skills/supabase-pentest-skills-0f9612276b49f241584f9d779767e35ae519875a/skills/extraction/supabase-extract-anon-key/SKILL.md`
- ...

## 触发条件

需要建立 HTTP/API/GraphQL/WebSocket/RPC/gRPC/后台任务/CLI/上传下载/模板渲染/URL fetch/权限边界/租户边界暴露面时触发。

## 执行步骤

1. 合并 02 的项目清单、03 的代码图谱、05 的 JS 发现。
2. 为每个暴露点记录 method、route、handler、参数、认证、授权、租户、输入来源、sink、风险标签。
3. 输出 `attack_surface.json`，供 07 候选生成和 06 动态验证。

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
