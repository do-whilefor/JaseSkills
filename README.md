<div align="center">

# JaseSkills

**Claude 安全 Skills、SecKB 知识库规则、JS 审计与授权测试工作流集合**

面向授权安全研究、代码审计、漏洞验证、AI 审计约束与安全知识库沉淀的个人 Skills 仓库。

![Status](https://img.shields.io/badge/status-active-brightgreen)
![Scope](https://img.shields.io/badge/scope-authorized%20security%20research-blue)
![Use](https://img.shields.io/badge/use-Claude%20Skills-purple)
![Safety](https://img.shields.io/badge/safety-non--destructive-orange)

</div>

---

## 项目简介

`JaseSkills` 是一个面向 Claude / Claude Code 的安全工作流仓库，用于整理、沉淀和复用安全审计相关的 Skills、规则文件、提示词、知识库资料和专项漏洞分析方法。

本仓库不是单一工具，而是一套围绕“授权范围内安全研究”的工程化资料集合，重点关注：

* 信息收集与项目结构理解
* JavaScript 审计与接口分析
* 越权、IDOR、SSRF、命令执行、反序列化、注入类等高价值漏洞专项研究
* SecKB 安全知识库建设
* 动态验证证据链设计
* AI 审计边界约束与反幻觉规则
* 漏洞质量门禁与无效漏洞过滤

目标是让 AI 在合法授权范围内更系统、更可复查、更少幻觉地完成安全分析任务。

---

## 核心定位

本仓库主要解决四类问题：

### 1. 让 Claude 更适合做安全审计

通过 `SKILL.md`、`CLAUDE.md`、规则文件和提示词，约束 Claude 在安全任务中按流程执行，而不是随意猜测结论。

### 2. 把安全经验沉淀为可复用 Skills

将信息收集、JS 审计、漏洞专项分析、动态验证、证据整理、报告判断等流程拆成可复用模块，方便长期迭代。

### 3. 降低 AI 幻觉和误报

仓库强调证据优先，要求区分：

* `candidate`：候选问题
* `needs_review`：需要人工复核
* `confirmed`：已验证问题
* `rejected`：无效问题

避免把工具输出、截图、猜测、静态代码片段直接当成漏洞结论。

### 4. 约束安全边界

所有内容默认用于合法授权的本地项目、靶场、CTF、SRC 授权范围或测试环境。动态验证应保持最小化、可回滚、无破坏。

---

## 仓库结构

| 目录                | 说明                                                       |
| ----------------- | -------------------------------------------------------- |
| `InforSkills`     | 信息收集相关 Skills，用于项目结构、接口、配置、依赖、暴露面梳理。                     |
| `Jscript审计Skills` | JavaScript 审计相关 Skills，关注前端接口、打包产物、SourceMap、参数、鉴权和业务逻辑。 |
| `ComplexSkills`   | 综合型安全审计 Skills，适合多阶段分析、动态验证和证据链组织。                       |
| `PoolSkills`      | 技能池 / 能力池资源，用于沉淀可复用的安全分析模块。                              |
| `SecKBSkills`     | SecKB 安全知识库 Skills，覆盖知识采集、索引、模板、规则、动态验证和质量门禁。            |
| `WafByPass`       | WAF 绕过方向的学习、研究和提示词资料。                                    |
| `Claude配置`        | Claude 本地配置、MCP 配置、规则文件和运行约束。                            |
| `规则文件`            | 面向 Claude 的统一执行边界、反幻觉规则和 loop / skills 约束。               |
| `提示词`             | 常用 Prompt、Web Prompt、Skills 生成提示词和强化提示词。                 |
| `IDOR`            | IDOR / BOLA 类型漏洞分析和动态验证思路。                               |
| `SSRF`            | SSRF 类型漏洞分析、边界约束和验证方法。                                   |
| `越权`              | 水平越权、垂直越权、权限边界绕过相关资料。                                    |
| `认证绕过`            | 登录、认证、Token、Session、JWT、OAuth 等认证绕过方向资料。                 |
| `业务逻辑`            | 优惠、订单、审批、状态机、邀请、重置密码等业务逻辑安全分析。                           |
| `多租户隔离`           | 多租户、组织、空间、项目、成员边界隔离问题分析。                                 |
| `任意文件上传-读取`       | 文件上传、任意文件读取、路径穿越、文件解析风险相关资料。                             |
| `命令执行`            | 命令执行、模板执行、危险函数调用等高风险问题研究。                                |
| `反序列化`            | 反序列化漏洞分析、动态验证和无害 marker 验证思路。                            |
| `注入类`             | SQL 注入、NoSQL 注入、模板注入、参数污染等注入类漏洞资料。                       |
| `PDF`             | PDF 文档分析、隐藏内容识别和文件审查相关资料。                                |

---

## 核心能力

### 信息收集

帮助 Claude 系统读取项目目录、配置文件、路由、依赖、接口、构建产物、历史文件和潜在暴露面，形成可追踪的信息图谱。

### JavaScript 审计

面向前端 JS、打包产物、懒加载资源、SourceMap、隐藏接口、GraphQL、WebSocket、前端未暴露参数、鉴权逻辑和业务状态流进行分析。

### 漏洞专项分析

按高价值漏洞类型组织审计思路，包括：

* 认证绕过
* 水平越权
* 垂直越权
* IDOR / BOLA
* SSRF
* 命令执行
* 反序列化
* 任意文件上传 / 读取
* 注入类漏洞
* 多租户隔离绕过
* 业务逻辑漏洞

### SecKB 知识库

`SecKBSkills` 用于构建和维护本地安全知识库，强调：

* 来源可信度
* 索引一致性
* 模板保真
* 动态验证证据
* 质量门禁
* 反幻觉
* 回归审计

### 动态验证证据链

严重漏洞不能只靠静态猜测下结论。候选问题应尽量转化为最小化、可回滚、无破坏的验证计划，并保留：

* 请求与响应
* 角色矩阵
* 租户矩阵
* 参数变化
* 日志证据
* 截图证据
* 影响边界
* 修复建议
* evidence manifest

---

## 使用方式

### 克隆仓库

```bash
git clone https://github.com/do-whilefor/JaseSkills.git
cd JaseSkills
```

### 查看某个 Skills 包

进入目标目录后，优先查看：

```text
README.md
SKILL.md
CLAUDE.md
CAPABILITY_INDEX.md
package-manifest.json
```

不同目录组织方式可能不同。如果目录中只有压缩包，可以先解压到 Claude Skills 目录或单独工作目录，再查看其中的 `SKILL.md`。

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
2. 读取目标项目结构
3. 读取规则文件和目标 Skill
4. 做信息收集与资产建模
5. 生成候选问题清单
6. 对候选问题做正向、反向、阻断和边界测试计划
7. 在本地、靶场或明确授权环境中做最小化动态验证
8. 整理证据链、影响说明、复现边界和修复建议
9. 证据不足时保持 needs_review，不升级为 confirmed
10. 删除无效漏洞、重复漏洞和无实际危害的问题
```

---

## 漏洞质量原则

本仓库更关注真实影响，而不是堆数量。

优先关注：

* 认证绕过
* 越权访问
* 多租户隔离绕过
* IDOR / BOLA
* SSRF
* 任意文件读取 / 写入
* 命令执行
* 反序列化
* 高影响注入
* 真实业务逻辑漏洞
* 可验证的信息泄露

默认不应单独报告低价值或无实际影响的问题，例如：

* 没有敏感信息的普通报错
* 只存在版本号但无法利用
* 无敏感影响的 CORS 配置
* 仅前端限制绕过但后端无影响
* 没有权限差异证明的接口猜测
* 没有数据越权结果的 ID 枚举猜测
* 没有动态验证证据的工具告警

信息泄露类问题应关注数据规模、敏感程度和可利用性。若只是少量无敏感内容，不应直接判定为有效漏洞。

---

## 安全边界

本仓库仅用于合法、授权、可控的安全研究、代码审计、学习和本地验证。

禁止用于：

* 未授权扫描、探测、利用或批量测试第三方目标
* DoS、DDoS、压测、资源耗尽或影响业务可用性的行为
* 删除、破坏、篡改数据库或业务数据
* 读取真实敏感数据来证明漏洞影响
* 持久化、横向移动、权限维持、钓鱼、撞库或社工攻击
* 绕过平台规则、SRC 规则或目标系统明确禁止的测试边界

建议所有动态验证都使用本地项目、靶场、测试数据库、可回滚数据、marker 文件、canary 服务和最小化请求完成。

---

## 适合人群

* 使用 Claude / Claude Code 做本地安全审计的人
* 做授权项目渗透测试、代码审计、JS 审计的人
* 维护个人安全知识库的人
* 想把提示词、规则、证据链和漏洞模板工程化沉淀的人
* 需要降低 AI 幻觉、提高审计可复查性的安全研究人员

---

## 后续维护建议

建议保持仓库结构清晰，避免重新堆积大量无用历史文件。

推荐规则：

* 每个 Skills 包保留清晰的 `README.md`、`SKILL.md` 和必要脚本
* 历史版本尽量放入 `历史` 目录或 GitHub Releases
* 大体积二进制文件建议移动到 Releases
* 每类漏洞目录都保留边界说明、验证约束、证据要求和不可报告条件
* 所有严重漏洞结论必须区分 `candidate`、`needs_review`、`confirmed`、`rejected`
* 不把 AI 猜测、工具告警或截图直接当作漏洞证据

---

## 个人维护命令

如果本地内容就是最终内容，推荐使用：

```powershell
cd "D:\Users\21452\Desktop\Skill"

git config --global core.longpaths true
git config core.longpaths true

if (Test-Path ".git\index.lock") {
    Remove-Item ".git\index.lock" -Force
}

git add -A -- . 2>&1 | Tee-Object git-add-log.txt

git status --short
git diff --cached --name-status | Select-Object -First 50

git commit -m "Update skills"
git push origin main
```

如果需要确认 GitHub 是否与本地一致：

```powershell
git status --short
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

当 `git rev-parse HEAD` 和 `git ls-remote origin refs/heads/main` 的哈希一致时，说明本地提交已经成功同步到 GitHub。

---

## GitHub About 建议

Description：

```text
Claude 安全 Skills、SecKB 知识库规则、JS 审计与授权测试工作流集合。
```

Topics：

```text
claude-skills
security-research
pentest
js-audit
seckb
prompt-engineering
web-security
ai-security
code-audit
bug-bounty
```

---

## 免责声明

本仓库内容仅用于合法授权的安全研究、学习、代码审计和本地测试。使用者应自行确保测试目标、测试方式和输出结果符合当地法律、平台规则、SRC 规则和授权范围。

任何未授权攻击、破坏性测试或滥用行为均与本仓库无关。
