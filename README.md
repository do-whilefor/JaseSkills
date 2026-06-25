# JaseSkills

<p align="center">
  <strong>Claude / Claude Code 安全审计 Skills 与授权测试工作流集合</strong>
</p>

<p align="center">
  用于安全审计、JS 分析、专项漏洞验证、SecKB 知识沉淀和 AI 审计边界约束。
</p>

<p align="center">
  <img alt="Scope" src="https://img.shields.io/badge/scope-authorized%20security%20research-blue">
  <img alt="Use" src="https://img.shields.io/badge/use-Claude%20%2F%20Claude%20Code-purple">
  <img alt="Safety" src="https://img.shields.io/badge/safety-evidence--driven-orange">
</p>

---

## 项目简介

`JaseSkills` 是一个面向 Claude / Claude Code 的安全工作流仓库，用于整理安全审计相关的 Skills、规则文件、提示词、知识库和专项漏洞分析方法。

它不是单一漏洞扫描器，也不是普通 Prompt 合集，而是将信息收集、JavaScript 审计、授权验证、业务逻辑分析、漏洞专项验证、证据链整理和 AI 反幻觉规则沉淀为可复用的工作流。

项目核心目标：

> 让 Claude 在合法授权范围内，更系统、更克制、更可复查地参与安全分析。

---

## 核心特点

* **面向 Claude / Claude Code**：提供可复用的安全 Skills、提示词和执行规则。
* **覆盖常见高价值漏洞**：包括 IDOR、越权、认证绕过、SSRF、命令执行、反序列化、注入类、任意文件上传 / 读取、多租户隔离和业务逻辑漏洞。
* **重视动态验证**：强调请求、响应、日志、截图、HAR、trace、角色矩阵、租户矩阵和 evidence manifest。
* **降低 AI 幻觉**：区分 `candidate`、`needs_review`、`confirmed`、`rejected`、`blocked`，避免把猜测当成漏洞结论。
* **强调安全边界**：默认仅用于本地项目、靶场、CTF、SRC 授权范围和明确授权的代码审计项目。

---

## 仓库结构

| 目录          | 说明                                         |
| ----------- | ------------------------------------------ |
| `Claude配置`  | Claude 本地配置、运行约束和规则文件                      |
| `规则文件`      | Claude / Codex / Loop / Skills 的执行边界和反幻觉规则 |
| `提示词`       | 通用 Prompt、Web Prompt、Skills 生成与强化提示词       |
| `Infor`     | 信息收集、项目结构、接口、配置、依赖和暴露面梳理                   |
| `Jscript`   | JavaScript 审计、前端接口、SourceMap、隐藏参数和业务逻辑分析   |
| `IDOR`      | IDOR / BOLA / 对象级越权分析                      |
| `越权`        | 水平越权、垂直越权和权限边界绕过                           |
| `认证绕过`      | 登录、Token、Session、JWT、OAuth、账号状态和接口门禁分析     |
| `多租户隔离`     | 组织、空间、项目、团队、租户边界验证                         |
| `业务逻辑`      | 订单、审批、邀请、重置密码、优惠、状态机等业务风险分析                |
| `SSRF`      | SSRF 风险分析、canary 验证和无害化验证                  |
| `命令执行`      | 命令拼接、危险函数、source-to-sink 路径分析              |
| `反序列化`      | 反序列化风险、输入可控性和动态验证                          |
| `注入类`       | SQL / NoSQL / 模板 / 参数污染等注入类问题              |
| `任意文件上传-读取` | 文件上传、读取、路径穿越、解压和对象存储 key 风险                |
| `WafByPass` | WAF 绕过学习资料和授权测试思路                          |
| `PDF`       | PDF 文档审查、资料归档和文件分析样例                       |

---

## 限制说明

列出未验证内容，不把未知内容包装成确定结论。
```

---

## 安全边界

本项目仅用于合法、授权、可控的安全研究、代码审计、学习和本地验证。

允许场景：

* 本地项目
* 自建靶场
* CTF / 练习环境
* SRC 授权范围
* 明确授权的代码审计项目
* 可控测试环境

禁止用于：

* 未授权扫描、探测、利用或批量测试第三方目标
* DoS、DDoS、压测或资源耗尽
* 删除、破坏、篡改数据库或业务数据
* 读取真实敏感数据来证明漏洞影响
* 持久化、横向移动、权限维持、钓鱼、撞库或社工攻击
* 绕过平台规则、SRC 规则或目标系统明确禁止的测试边界

---

## 适合人群

* 使用 Claude / Claude Code 做安全审计的人
* 做授权项目渗透测试、代码审计、JS 审计的人
* 维护个人安全知识库的人
* 希望把 Prompt、规则、证据链和漏洞模板工程化沉淀的人
* 需要降低 AI 幻觉、提高审计可复查性的安全研究人员

---

## 项目理念

只有具备明确影响、清晰边界和可验证证据的问题，才应被推进为 `confirmed`。证据不足的问题应保留为 `candidate` 或 `needs_review`，无实际危害或缺少权限差异证明的问题应被过滤。

> 让 AI 安全审计从“会猜”变成“可验证、可复查、可沉淀”。

---

## License

请根据实际授权情况补充 License。
