---
name: vuln-md
description: 根据用户提供或在明确授权范围内验证的漏洞事实，稳定生成固定结构的中文 Markdown 漏洞报告。用于漏洞赏金、SRC、未授权访问、越权、信息泄露、硬编码凭据、调试端点暴露等报告；支持每个复现步骤包含多个原始 HTTP/Yakit 报文、curl 命令、脚本、浏览器或 App 操作，以及多个响应和结果证据。
---

# 漏洞 Markdown 报告

将报告、证据文件或授权验证结果整理成规范的 `.md`。始终使用生成器输出最终报告，不要手写或自由调整章节，以确保相同输入产生完全相同的结果。

## 工作流

1. 阅读用户提供的 Markdown、JSON、文本、截图说明或原始流量，按 `references/report-input.example.json` 建立结构化 JSON。
2. 只写已提供或实际验证的事实。不得为了补齐报告而猜测请求头、响应、状态码、数据字段、Payload、影响规模或漏洞等级。
3. 如用户明确要求 AI 复现，并明确给出授权范围，执行最小、只读、单样本验证；记录实际工具、输入、响应和结果。生成报告本身不构成访问目标的授权。不得批量枚举、拖库、写入、改密、破坏或扩大测试范围。
4. 运行固定生成器：

   ```powershell
   python scripts/generate_report.py --input report.json --output report.md
   ```

   正式模式默认严格校验。证据不完整时仅可显式使用 `--draft`，输出会显示草稿警告和 `待补充`。
5. 检查输出无占位内容、事实与证据一致、代码块可复制，再交付 `.md`。

## 稳定性要求

- 最终报告只能由 `scripts/generate_report.py` 生成，禁止临时增删标题、改编号、改字段名或改变章节顺序。
- 固定顺序为：标题、基本信息、漏洞简述、漏洞 URL/功能点、影响参数、复现步骤、修复建议。
- 域名、功能点、参数、步骤、证据块和建议均保持 JSON 中的原始顺序；不自动排序、不添加当前时间、不生成随机编号。
- 使用 UTF-8、LF 换行、固定空行和确定性的 Markdown 围栏。同一份 JSON 输入必须生成字节一致的 `.md`。
- 漏洞标题使用“厂商 - 漏洞点存在漏洞类型漏洞”格式。漏洞简述只写概况、攻击条件和危害，不写 URL、具体 Payload、命令或数据包。
- 正式报告不得出现 `待补充`、伪造证据或未验证的肯定表述。推测只能明确写为“未验证风险”。

## 多种复现入口

每个 `steps[]` 使用固定字段：`title`、`method`、`preconditions`、`description`、`inputs`、`outputs`、`result`。

- `inputs` 是可扩展数组，可同时放多个入口：Yakit/原始 HTTP 请求包、curl 命令、Python/Yak 脚本、浏览器操作、App 操作、Payload 或其他输入。
- `outputs` 是可扩展数组，可同时放多个证据：原始 HTTP 响应、终端输出、页面结果、App 结果、日志或其他结果。
- 每个输入/输出块使用 `label`、`kind`、`language`、`content`；可选 `replayable` 表示内容是否声称可直接重放。
- 当 `replayable: true` 且 `kind` 为 `http-request`/`http-response` 时，生成器强制校验 HTTP/1.x 起始行、头部空行和请求 `Host`。其他方式不要求伪装成 Yakit 数据包。
- 同一步可以有任意多个输入和输出块，但正式模式至少各有一个。按实际复现顺序填写数组，不要把摘要当作真实输出。

## 必填内容

顶层必填：`title`、`domain`、`vulnerability_type`、`severity`（仅 `严重`/`高危`/`中危`/`低危`）、`summary`、`location`、`affected_parameters`、`steps`、`recommendations`。

`domain`、`location` 可为字符串或字符串数组；`affected_parameters`、`recommendations` 必须为非空数组。无影响参数时明确填写 `无`。

## 固定输出结构

```markdown
# <漏洞标题>

## 基本信息
<固定五行信息表>

## 1. 漏洞简述
## 2. 漏洞 URL / 功能点
## 3. 影响参数
## 4. 复现步骤
### 步骤 N：<标题>
#### 输入 / 操作 N：<标签>
#### 响应 / 结果 N：<标签>
## 5. 修复建议
```

不得新增“技术分析”“危害分析”“证据摘要”等游离章节；相关内容归入已有栏目或复现证据块。

## 证据与隐私

保留提交所需的最小证据。正文可掩码真实手机号、邮箱、Token、Cookie、密码和签名 URL；如用户明确要求平台提交完整 PoC，仅在其授权的证据块中保留原值。不得将失败尝试、猜测结果或未执行命令描述为已复现。

## 生成器

使用 `scripts/generate_report.py` 校验输入并生成最终 Markdown。脚本不联网、不访问目标、不生成利用载荷；AI 复现行为必须在调用脚本之前独立完成并满足上述授权边界。
