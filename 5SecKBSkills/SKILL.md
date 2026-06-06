---
name: seckb
description: "SecKB 本地安全知识库、漏洞模板、SRC规则、工具release学习与审计路由入口。"
---

# seckb

这是集合型 Claude Skill 的顶层入口。

触发本 Skill 后，优先读取内部主入口文件：


然后根据用户任务继续读取同目录下的 README、docs、templates、scripts、knowledgebase、子 Skill 或 dispatcher。

## 使用规则

1. 先确认任务边界和授权范围。
2. 优先由内部 master、dispatcher 或 orchestrator 做任务分发。
3. 不把工具告警、关键词命中、单次异常响应直接当成漏洞。
4. 漏洞结论必须有代码证据、动态证据、影响证据和误报排除。
5. 遇到具体漏洞类型时，优先调用内部模板、知识库和质量门禁。
