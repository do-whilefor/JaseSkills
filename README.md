<div align="center">

# JaseSkills

面向 Claude 的安全 Skills、知识库规则与授权测试工作流集合。  
聚焦信息收集、JavaScript 审计、动态验证证据链、安全知识库建设、漏洞分类研究与 AI 审计边界治理。

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Scope](https://img.shields.io/badge/scope-authorized%20security%20research-blue)
![Use](https://img.shields.io/badge/use-local%20LLM%20%7C%20Claude%20Skills-purple)
![Safety](https://img.shields.io/badge/safety-boundary%20first-red)

</div>

---

## 项目定位

`JaseSkills` 是一个用于整理、沉淀和复用 Claude 安全工作流的个人仓库。它不是单一工具，而是一套围绕“授权范围内安全研究”的 Skills、规则、模板、提示词和知识库资料集合。

本仓库重点解决以下问题：

- 如何让 Claude 在本地授权项目中更系统地完成信息收集、代码理解和安全审计。
- 如何把 JS 文件、接口、参数、权限边界、业务逻辑、动态验证证据链组织成可复用流程。
- 如何降低 AI 幻觉，避免把工具告警、猜测、截图或未验证线索误判成 confirmed 漏洞。
- 如何把安全知识库、漏洞模板、审计规则和动态验证流程沉淀为长期可维护的工作资产。

---

## 仓库结构

| 目录 | 说明 |
|---|---|
| [`1InforSkills`](./1InforSkills) | 信息收集相关 Skills，包含信息收集流程、历史版本和压缩包资源。 |
| [`2Jscript审计Skills`](./2Jscript审计Skills) | JavaScript 收集、还原、接口分析、参数提取和前后端审计相关 Skills。 |
| [`3ComplexSkills`](./3ComplexSkills) | 综合型安全审计 Skills，适合多阶段分析、动态验证和证据链组织。 |
| [`4PoolSkills`](./4PoolSkills) | 技能池/能力池类资源，用于沉淀可复用的安全分析模块。 |
| [`5SecKBSkills`](./5SecKBSkills) | SecKB 安全知识库 Skills，覆盖知识采集、索引、模板、规则、动态验证、质量门禁和回归审计。 |
| [`6WafByPass`](./6WafByPass) | WAF 绕过方向的学习与研究资料。 |
| [`Claude配置`](./Claude配置) | Claude 本地配置、规则文件、MCP 配置和运行约束。 |
| [`提示词`](./提示词) | 常用提示词、Web Prompt、Skills 生成提示词和强化提示词。 |
| [`规则文件`](./规则文件) | 面向 Claude 的统一边界规则与项目执行规范。 |
| [`第三方源码Skills`](./第三方源码Skills) | 第三方源码审计与安全分析相关 Skills。 |
| [`IDOR`](./IDOR) / [`SSRF`](./SSRF) / [`越权`](./越权) / [`认证绕过`](./认证绕过) | 按漏洞类型整理的专项分析与动态验证思路。 |
| [`业务逻辑`](./业务逻辑) / [`多租户隔离`](./多租户隔离) | 面向真实业务流程、租户边界和状态机的审计资料。 |
| [`任意文件上传-读取`](./任意文件上传-读取) / [`命令执行`](./命令执行) / [`反序列化`](./反序列化) / [`注入类`](./注入类) | 高风险漏洞类型的专项流程、提示词和验证约束。 |
| [`PDF`](./PDF) | PDF 文档分析、隐藏内容识别和文件审查相关资料。 |

---

## 核心能力

### 1. 信息收集

用于帮助 Claude 系统读取项目结构、配置文件、路由、依赖、接口、历史文件、构建产物和潜在暴露面。目标不是简单列目录，而是形成可追踪、可复查、可继续分析的信息图谱。

### 2. JavaScript 审计

面向前端 JS、打包产物、懒加载资源、SourceMap、隐藏接口、前端未暴露参数、后端可接受参数、GraphQL、WebSocket、鉴权逻辑和业务状态流进行分析。

### 3. SecKB 安全知识库

`5SecKBSkills` 用于构建和维护本地安全知识库，强调来源可信度、索引一致性、模板保真、动态验证证据、质量门禁、反幻觉和回归审计。

### 4. 动态验证证据链

本仓库强调：严重漏洞不能只靠静态猜测下结论。候选问题应尽量转化为最小化、可回滚、无破坏的验证计划，并保留请求、响应、截图、日志、角色矩阵、租户矩阵和 evidence manifest。

### 5. AI 审计边界治理

仓库内规则文件用于约束 Claude：

- 不把 candidate 伪装成 confirmed。
- 不把工具输出当作最终证据。
- 不编造动态验证结果。
- 不越过授权范围。
- 不执行破坏性测试。
- 不读取真实敏感数据来证明影响。

---

## 使用方式

### 克隆仓库

```bash
git clone https://github.com/do-whilefor/JaseSkills.git
cd JaseSkills
```

### 使用某个 Skills 包

进入对应目录，优先查看：

```text
README.md
SKILL.md
CAPABILITY_INDEX.md
CLAUDE.md
package-manifest.json
```

不同目录的组织方式不完全一致。如果目录中只有压缩包，可以先解压到 Claude Skills 目录或单独工作目录中，再查看其中的 `SKILL.md`。

### Windows 下常见 Claude Skills 目录

```powershell
$skillsRoot = "$env:USERPROFILE\.claude\skills"
```

示例：

```powershell
Expand-Archive -Path .\YourSkill.zip -DestinationPath $skillsRoot -Force
```

安装后建议先让 Claude 读取对应的 `SKILL.md`、能力索引和边界规则，再开始执行具体任务。

---

## 推荐工作流

```text
1. 明确授权范围
2. 读取规则文件和目标 Skill
3. 做信息收集与项目结构建模
4. 生成候选问题清单
5. 对候选问题做正向/反向/阻断/边界测试计划
6. 在本机、靶场或明确授权环境中做最小化动态验证
7. 生成证据链、影响说明、复现边界和修复建议
8. 证据不足时保持 needs_review，不升级为 confirmed
```

---

## 安全边界

本仓库仅用于合法、授权、可控的安全研究、代码审计、学习和本地验证。

禁止用于：

- 未授权扫描、探测、利用、绕过或批量测试第三方目标。
- DoS、DDoS、压测、资源耗尽或影响业务可用性的行为。
- 删除、破坏、篡改数据库或业务数据。
- 读取真实敏感数据来证明漏洞影响。
- 持久化、横向移动、权限维持、钓鱼、撞库或社工攻击。
- 绕过平台规则、SRC 规则或目标系统明确禁止的测试边界。

建议所有动态验证都使用本地项目、靶场、测试数据库、可回滚数据、marker 文件、canary 服务和最小化请求完成。

---

## 适合人群

- 使用 Claude / Claude Code 做本地安全审计的人。
- 做授权项目渗透测试、代码审计、JS 审计或安全知识库维护的人。
- 希望把提示词、规则、证据链和漏洞模板工程化沉淀的人。
- 需要降低 AI 幻觉、提高审计可复查性的安全研究人员。

---

## 后续维护建议

保持仓库清晰比堆叠文件更重要。后续建议：

- 每个 Skills 包保留清晰的 `README.md`、`SKILL.md` 和最小必要脚本。
- 历史版本放入 `历史` 或 Releases，避免根目录长期堆积压缩包。
- 大体积二进制文件建议移动到 Releases，避免仓库体积过大。
- 每类漏洞目录都保留边界说明、验证约束、证据要求和不可报告条件。
- 所有“严重漏洞”结论必须区分 `candidate`、`needs_review`、`confirmed`、`rejected`。

---

## 维护命令


```powershell

git config --global core.longpaths true
git config core.longpaths true

if (Test-Path ".git\index.lock") {
    Remove-Item ".git\index.lock" -Force
}

git add -A -- . 2>&1 | Tee-Object git-add-log.txt

git status --short
git diff --cached --name-status | Select-Object -First 50

git commit -m "Update skills"
git push origin HEAD:main --force
```

---

## GitHub About 建议

Description：

```text
Claude 安全 Skills、SecKB 知识库规则、JS 审计与授权测试工作流集合。
```

Topics：

```text
claude-skills, security-research, pentest, js-audit, seckb, prompt-engineering, web-security, ai-security, code-audit
```

---

## 免责声明

本仓库内容仅用于合法授权的安全研究、学习、代码审计和本地测试。使用者应自行确保测试目标、测试方式和输出结果符合当地法律、平台规则、SRC 规则和授权范围。任何未授权攻击、破坏性测试或滥用行为均与本仓库无关。
