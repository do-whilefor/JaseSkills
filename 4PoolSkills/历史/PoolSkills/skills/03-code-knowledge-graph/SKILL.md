---
name: 03-code-knowledge-graph
description: 路由、控制器、服务、DAO、模型、权限中间件、数据流、调用图、source/sink、跨文件链路
---

# 03-code-knowledge-graph

路由、控制器、服务、DAO、模型、权限中间件、数据流、调用图、source/sink、跨文件链路

## 原始来源映射

本 skill 合并/承接 29 个原始 `SKILL.md` 的相关能力。代表来源：

- `MyuriKanao-src-hunter-skill/src-hunter-skill-978b95318163656c5d2d9902dbe6c5ea54c7e800/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/bug-bounty/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/web2-vuln-classes/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-solidity-audit-mcp/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/audit-context-building/skills/audit-context-building/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/building-secure-contracts/skills/audit-prep-assistant/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/c-review/skills/c-review/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/constant-time-analysis/skills/constant-time-analysis/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/entry-point-analyzer/skills/entry-point-analyzer/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/semgrep-rule-creator/skills/semgrep-rule-creator/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/semgrep-rule-variant-creator/skills/semgrep-rule-variant-creator/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/sharp-edges/skills/sharp-edges/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/static-analysis/skills/codeql/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/static-analysis/skills/semgrep/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/crypto-protocol-diagram/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/genotoxic/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/graph-evolution/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/mermaid-to-proverif/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/trailmark/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/trailmark-structural/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/trailmark/skills/vector-forge/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/variant-analysis/skills/variant-analysis/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/formats/transilience-report-style/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/api-security/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/attack-path-stitcher/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/cryptography/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/firewall-review/SKILL.md`
- `transilienceai-communitytools/communitytools-0f06ed314493e7f3b1da30de4d5ad0d4cb85d5bf/skills/source-code-scanning/SKILL.md`

## 触发条件

需要跨文件理解路由、handler、权限、参数、模型、查询、危险函数、数据流或 source/sink 时触发。

## 执行步骤

1. 优先调用 Babel、TypeScript Compiler API、tree-sitter、Python ast/libcst、JavaParser、PHP-Parser、Ruby Ripper、Go parser、Rust syn。
2. 插件不可用时退化为安全 regex/grep 候选，但必须标记置信度。
3. 构建文件、模块、类、函数、路由、参数、认证/权限、模型、查询、文件、网络、命令、模板、反序列化、上传/下载、source、sink、evidence、report 节点。
4. 输出 `route_graph.json` 和 `dangerous_sinks.json`。

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
