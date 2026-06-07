# deserialization-local-verify

`deserialization-local-verify` 是从 `反序列化转skills.txt` 复刻出的单一 Claude Skill，用于本地授权项目的反序列化暴露面分析、无害动态验证、证据链审计和结果降级反查。

## Skill 数量

最终只保留 1 个主 Skill。TXT 的所有内容都围绕同一条任务链：识别本地项目语言生态与依赖，搜索反序列化 source/sink，建立暴露地图，设计并执行无害动态验证，用证据门槛判定 confirmed/candidate/blocked/not reachable/dependency-only，再做反向审判。拆成多个 Skills 会造成上下文断裂和状态判定不一致。

## 目录结构

```text
deserialization-local-verify/
  SKILL.md
  README.md
  templates/
    output-template.md
  checklists/
    quality-gate.md
    final-review.md
  examples/
    basic-example.md
    full-example.md
  tests/
    skill-quality-tests.md
```

未保留额外的 `rules/`、`workflows/`、`schemas/`、`fixtures/` 目录。TXT 的规则、流程、模板和门禁已由上述 8 个文件承载。

## 调用方式

```text
使用 deserialization-local-verify Skill。目标项目路径是 <path>。授权范围是 <local-scope>。只允许访问本地项目、本地测试服务、本地测试数据库、本地队列、本地缓存和指定测试目录。请先建立反序列化暴露地图，再把 candidate 转成本地无害动态验证。没有动态证据不得标记 confirmed。
```

## 必要输入

- 本地项目路径。
- 授权边界：本地路径、端口、数据库、队列、缓存、目录。
- 运行方式：测试、服务、worker、CLI 命令。
- 测试账号、角色、租户和 token 生成方式。
- 可写测试目录。
- 允许修改的测试目录。

缺失输入不得伪造成已验证。对应结论必须写“未验证”或保持 candidate。

## 交付验收

合格输出必须满足：

- 有项目语言、框架、目录、依赖识别证据。
- 有 source/sink 搜索记录。
- 有依赖存在、项目调用、输入来源、安全控制、动态验证可能性的分离判断。
- 每个 candidate 有正向样本、负向样本、阻断样本、marker、观测和清理计划。
- 每个 confirmed 有 source、sink、调用链、本地动态验证、无害 marker、日志或断言、清理记录、修复建议、回归测试建议。
- 没有动态证据的结论必须是 candidate、blocked、not reachable、dependency-only、false positive 或未验证。
- 有降级清单、补测清单、漏报追查清单和强制自我反查。
- 不包含公网、生产、破坏性 payload、真实恶意 gadget、命令执行、外连、反弹或 DoS 验证。

## 文件作用

| 文件 | 作用 |
|---|---|
| SKILL.md | Claude 调用的核心规则、流程、门禁、状态判定、失败处理和 TXT 映射 |
| templates/output-template.md | 最终报告模板、证据字段、降级表、补测表、漏报追查表 |
| checklists/quality-gate.md | 执行中门禁，防止把静态命中或依赖存在写成漏洞 |
| checklists/final-review.md | 交付前反向审判和 confirmed 降级清单 |
| examples/basic-example.md | 最小示例，展示 candidate、blocked、dependency-only 的写法 |
| examples/full-example.md | 完整示例，展示多入口、多状态、动态证据与降级补测 |
| tests/skill-quality-tests.md | 检查是否漏复刻、幻觉扩展、空壳、命名失败、缺质量门禁 |
