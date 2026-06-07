# Local Auth Gate Audit

`local-auth-gate-audit` 是从 TXT《提示词转skills.txt》的核心内容转成的单一 Claude Skill。它用于在本地授权范围内，对开源项目的认证、会话、权限门禁、账号状态、接口访问控制一致性做动态验证闭环。

## 核心用途

让 Claude 在本地授权项目中完成以下工作：

1. 读取项目结构、启动方式、认证模块、权限模块、路由和依赖。
2. 建立认证与门禁暴露面矩阵。
3. 准备测试数据库、seed、fixture 和测试身份。
4. 执行正向与反向动态验证。
5. 覆盖 REST、GraphQL、WebSocket、文件、导出、异步任务、Webhook、邀请、重置、邮箱绑定、OAuth 等实际存在的入口。
6. 用 evidence 证据目录区分 `confirmed`、`candidate`、`blocked`、`false_positive`、`needs_review`。
7. 对证据不足的 confirmed 执行降级。

## Skill 数量

只保留 1 个主 Skill。

原因：TXT 只有一个连续目标：本地授权认证门禁动态验证。GraphQL、WebSocket、文件接口、异步任务、OAuth、邀请、重置密码等不是独立任务，而是同一认证门禁验证闭环的入口类型。拆成多个 Skills 会重复账号矩阵、evidence、暴露面矩阵和质量门禁。

## 目录说明

| 文件 | 作用 | 来源类型 |
|---|---|---|
| `SKILL.md` | 主执行规则、范围、流程、门禁、输出格式、映射说明 | 原文复刻 + 工程化补强 |
| `templates/output-template.md` | 报告、findings、replay、30 类测试计划可填写模板 | 原文复刻 + 工程化补强 |
| `checklists/quality-gate.md` | Skill 交付门禁与认证验证门禁 | 原文复刻 + 工程化补强 |
| `checklists/final-review.md` | 交付前追责反查清单 | 原文复刻 + 工程化补强 |
| `examples/basic-example.md` | 最小本地 Web 项目调用示例 | 工程化补强 |
| `examples/full-example.md` | 完整证据链、候选降级、blocked 示例 | 工程化补强 |
| `tests/skill-quality-tests.md` | 检测漏复刻、幻觉扩展、空壳文件、命名失败 | 工程化补强 |

## 调用输入

向 Claude 调用本 Skill 时，提供以下信息。缺失项由 Claude 先在仓库内查找；仍找不到时输出 blocked 和最小补齐方案。

```text
项目路径：
本地服务地址：
测试数据库方式：
测试账号或 seed 方式：
授权边界：
是否允许创建 evidence/：
是否允许创建 tests/security/：
```

## 最低输出

一次合格执行至少应产生：

```text
evidence/run-manifest.json
evidence/routes.json
evidence/auth_surface_matrix.md
evidence/test_accounts.json
evidence/replay_results.json
evidence/findings.md
```

如使用 Playwright 或浏览器验证，还应保存：

```text
evidence/har/
evidence/traces/
evidence/screenshots/
```

如果服务未启动、测试账号缺失、测试数据库缺失或授权边界不清，`findings.md` 不能出现 confirmed。

## 结论规则

- `confirmed`：有真实动态请求、正反对照、异常成功或越权效果、证据文件、修复建议和回归测试。
- `candidate`：有风险假设和复现实验计划，但缺动态证据或关键证据。
- `blocked`：缺启动命令、账号、DB、环境、授权边界或回滚能力。
- `false_positive`：通过正反测试排除。
- `needs_review`：信息冲突或证据不足，不能归入其他等级。

## 禁止范围

本 Skill 不用于公网扫描、第三方系统、真实用户数据、中间人攻击、流量劫持、证书劫持、钓鱼、社工、DoS、压力测试、不可回滚写操作或生产数据库验证。

## 维护规则

再次修改本 Skill 时，必须重新读取原始 TXT 和全部 Skill 文件。未读取的文件必须标记为“未验证，不得宣称已通过”。新增内容必须标明是工程化补强，不得伪装为 TXT 原文。
