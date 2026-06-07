---
name: 02-project-intelligence
description: 项目结构、语言、框架、配置、依赖、入口点、构建方式、运行方式识别
---

# 02-project-intelligence

项目结构、语言、框架、配置、依赖、入口点、构建方式、运行方式识别

## 原始来源映射

本 skill 合并/承接 145 个原始 `SKILL.md` 的相关能力。代表来源：

- `Eyadkelleh-awesome-claude-skills-security/awesome-claude-skills-security-86d2316b278ac266b5407a7b23d0b8c294dd0e54/seclists-categories/web-shells/SKILL.md`
- `Eyadkelleh-awesome-claude-skills-security/awesome-claude-skills-security-86d2316b278ac266b5407a7b23d0b8c294dd0e54/seclists-categories fuzzing/fuzzing/SKILL.md`
- `Eyadkelleh-awesome-claude-skills-security/awesome-claude-skills-security-86d2316b278ac266b5407a7b23d0b8c294dd0e54/seclists-categories passwords/passwords/SKILL.md`
- `Eyadkelleh-awesome-claude-skills-security/awesome-claude-skills-security-86d2316b278ac266b5407a7b23d0b8c294dd0e54/seclists-categories pattern-matching/pattern-matching/SKILL.md`
- `Eyadkelleh-awesome-claude-skills-security/awesome-claude-skills-security-86d2316b278ac266b5407a7b23d0b8c294dd0e54/seclists-categories payloads/payloads/SKILL.md`
- `Eyadkelleh-awesome-claude-skills-security/awesome-claude-skills-security-86d2316b278ac266b5407a7b23d0b8c294dd0e54/seclists-categories usernames/usernames/SKILL.md`
- `Eyadkelleh-awesome-claude-skills-security/awesome-claude-skills-security-86d2316b278ac266b5407a7b23d0b8c294dd0e54/seclists-categories web-shells/web-shells/SKILL.md`
- `MyuriKanao-src-hunter-skill/src-hunter-skill-978b95318163656c5d2d9902dbe6c5ea54c7e800/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/bb-methodology/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/bug-bounty/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/report-writing/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/security-arsenal/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/triage-validation/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/web2-recon/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/web2-vuln-classes/SKILL.md`
- `shuvonsec-claude-bug-bounty/claude-bug-bounty-12c1164a192c259565bb175ca6019bf7bb2ea214/skills/web3-audit/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-ai-tools/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-bug-classes/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-case-study-role-misconfig/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-grep-arsenal/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-hunt-foundation/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-hunt-zksync-era/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-methodology-research/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-poc-foundry/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-solidity-audit-mcp/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-start-here/SKILL.md`
- `shuvonsec-web3-bug-bounty-hunting-ai-skills/web3-bug-bounty-hunting-ai-skills-41238d812685525e66b0591bb64de9cd0ac956d3/web3-triage-report/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/.codex/skills/gh-cli/SKILL.md`
- `trailofbits-skills/skills-c94841be3deae8a880fa1a9078979adac7ca3dbc/plugins/agentic-actions-auditor/skills/agentic-actions-auditor/SKILL.md`
- ...

## 触发条件

需要识别项目结构、语言、框架、配置、依赖、构建/运行方式、入口点或环境风险时触发。

## 执行步骤

1. 递归枚举文件和目录，排除 node_modules/vendor/.git 等大体积目录但保留 lock/config。
2. 识别 package.json、requirements、pyproject、Pipfile、pom.xml、build.gradle、composer.json、go.mod、Cargo.toml、Gemfile。
3. 识别 Dockerfile、compose、nginx/Apache、CI/CD、env 示例、cloud/framework/auth/CORS/session/cookie/upload/storage/database/cache/queue 配置。
4. 识别 Express/Koa/Fastify/Nest/Next/Nuxt/Vue/React/Angular/Django/Flask/FastAPI/Spring/Rails/Laravel/Symfony/Gin/Echo/Fiber/Axum/Actix/Rocket/Electron/Extension/小程序。
5. 输出 `project_inventory.json` 并交给 03/04。

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
