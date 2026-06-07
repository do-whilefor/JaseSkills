# authz-bypass-dynamic-audit

## 用途

将《越权提示词转skills.txt》落地为 1 个可执行 Claude Skill，用于本地授权开源项目的越权动态验证。

它驱动 Claude 完成：项目画像、越权暴露面矩阵、多角色/多租户动态验证、evidence/ 证据闭环、confirmed 误报追责、candidate 最小复现计划、blocked 补齐方法、false_positive 排除依据、50 项非常规路径测试、修复建议和回归测试。

## 调用前提

| 条件 | 要求 |
|---|---|
| 授权边界 | 只能是本机、授权开源项目、本地服务、测试账号、测试租户、测试数据库、测试文件和测试资源 |
| 禁止动作 | 不扫描公网、不攻击第三方、不使用真实用户数据、不做劫持/钓鱼/社工、不做 DoS/爆破、不删除数据库、不破坏业务、不改生产逻辑造洞 |
| 结论限制 | 没有动态请求、正反对照、证据文件时不得写 confirmed |

## 推荐调用格式

```text
使用 authz-bypass-dynamic-audit。
项目路径：C:\work\demo-app
授权范围：仅限本机项目、本地测试数据库、本地测试账号和本地测试租户。
要求：先生成 authz_surface_matrix.md，再启动本地服务，创建测试身份和测试资源，执行动态验证。
```

## 输入

| 输入 | 示例 | 缺失处理 |
|---|---|---|
| 项目路径 | `C:\work\demo-app` | blocked |
| 授权范围 | `仅限本机和测试数据库` | 不做动态请求 |
| 本地服务信息 | `http://127.0.0.1:3000` | 从启动日志识别；失败则 blocked |
| 测试数据库说明 | `.env.test`、docker compose、SQLite 测试库 | blocked 或最小 fixture 计划 |
| 账号/资源创建方式 | seed、fixture、注册接口、测试工厂 | blocked 或最小 fixture 计划 |

## TXT 原文要求的 evidence/ 目录

```text
evidence/
  authz_surface_matrix.md
  test_accounts.json
  test_resources.json
  replay_plan.md
  replay_results.json
  findings.md
  false_positives.md
  blocked.md
  har/
  traces/
  screenshots/
  logs/
  curl/
  tests/
```

可选工程化补强：`evidence/_index.md`，用于索引证据文件；它不是 TXT 原文要求。

## 结论等级

| 等级 | 条件 |
|---|---|
| confirmed | 真实动态请求、正反样本、异常成功结果、证据文件、可复现步骤全部存在 |
| candidate | 代码路径可疑，但没有完整动态证据 |
| blocked | 环境、账号、依赖、启动、数据缺失导致无法验证 |
| false_positive | 动态验证证明拒绝访问或没有越权效果 |
| needs_review | 证据不完整，影响判断不稳定，需要人工复核 |

## 文件说明

| 文件 | 作用 | 来源类型 |
|---|---|---|
| `SKILL.md` | 主执行规则，包含范围、输入、输出、流程、门禁、分级、追责和 TXT 映射 | 原文复刻 + 工程化补强 |
| `templates/output-template.md` | 最终 13 部分报告模板、evidence 文件模板、UC-01 到 UC-50 矩阵 | 原文复刻 |
| `checklists/quality-gate.md` | 交付质量门禁，防止未读 TXT、命名失败、空壳文件、无证据 confirmed | 原文复刻 + 工程化补强 |
| `checklists/final-review.md` | confirmed 25 项追责和漏测反查 | 原文复刻 |
| `examples/basic-example.md` | 单 REST 资源的正反对照示例 | 工程化补强 |
| `examples/full-example.md` | REST、文件、GraphQL、WebSocket、异步任务组合示例 | 工程化补强 |
| `tests/skill-quality-tests.md` | 检查 Skill 是否漏复刻、幻觉扩展、空壳、不可执行 | 工程化补强 |

## 交付标准

1. 只保留 1 个主 Skill。
2. 不存在空目录和空壳文件。
3. 所有 confirmed 都有动态证据。
4. 所有 candidate 都有最小复现计划。
5. 所有 blocked 都有补齐方法。
6. 所有 false_positive 都有排除依据。
7. 原文复刻和工程化补强在映射表中分开标注。
