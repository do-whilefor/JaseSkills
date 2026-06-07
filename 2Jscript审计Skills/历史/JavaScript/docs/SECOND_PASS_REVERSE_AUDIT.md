# 第二轮反向审查规则

本文件用于约束对上一轮 JS 安全审计 Skills 评估结果的二次反审。二次反审的核心原则是：不维护原结论，不用文档完整度替代实现强度，不用模板和 fixture 替代真实 detector，不用工具名出现替代 runtime ready。

## 强制降级规则

| 情况 | 必须写法 |
| --- | --- |
| 无文件证据 | 未证实 |
| 只有 Markdown 或 JSON 矩阵 | doc-only |
| 只有 grep/regex/关键词 | candidate-only，不是语义审计 |
| 无 Playwright/Burp/HAR 请求响应证据 | 未动态验证 |
| 无多角色/多租户回放 | 缺少 role/tenant replay |
| 无 positive/negative/blocked/needs_review 样本 | 测试不足 |
| 无 schema 强校验 | 证据不可强校验 |
| 无 report mapping | 无法闭环到报告 |
| 无 quality gate | 无法量化质量 |

## 二次反查范围

必须反查：原评估结论、30 个 JS 收集点、20 个 JS 审计语义能力、25 个严重 JS 漏洞链、所有参与评估文件、评分虚高、P0/P1/P2 可执行性、40 个偏门 JS 审计点。

## 不破坏保真要求

任何修复不得删除 `knowledge/`、`templates/`、原有 `SKILL.md`、原有能力矩阵。新增能力必须以附加文件、附加测试、附加脚本方式落地，除非明确是在修复拼写、路由或自检引用。
