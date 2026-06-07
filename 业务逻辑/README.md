# business-logic-verify

`business-logic-verify` 是从 `业务逻辑转skills.txt` 提取核心主题后命名的单一 Claude Skill。它用于本地授权开源项目的业务逻辑漏洞动态验证、证据采集、分级、复核和最终报告。

## Skill 数量决策

保留 1 个主 Skill。TXT 中的内容属于同一条连续任务链：边界确认、项目理解、十类业务逻辑方向、replay plan、动态验证、证据要求、输出报告、第一轮反思、第二轮补挖、confirmed 反向审判。拆分会造成 Claude 在项目画像、证据编号和最终分级之间重复传递上下文，增加误判风险。

## 目录说明

| 文件 | 作用 | 来源类型 |
|---|---|---|
| `SKILL.md` | Claude 调用入口；包含范围、输入、输出、工作流、质量门禁、失败处理、TXT 映射 | 原文复刻 + 工程化补强 |
| `templates/output-template.md` | 最终报告模板；提供可填写字段和证据编号 | 原文复刻 + 工程化补强 |
| `checklists/quality-gate.md` | 执行前、执行中、结论前的门禁 | 原文复刻 + 工程化补强 |
| `checklists/final-review.md` | 第一轮反思、第二轮补挖、confirmed 20 项审判 | 原文复刻 |
| `examples/basic-example.md` | 最小示例，展示静态可疑点不得 confirmed | 工程化补强 |
| `examples/full-example.md` | 完整示例，展示报告结构和降级逻辑 | 工程化补强 |
| `tests/skill-quality-tests.md` | 验收 Skill 是否漏复刻、摘要化、幻觉扩展、命名失败或空壳 | 工程化补强 |

## 调用方式

向 Claude 提供本地项目和测试环境信息：

```text
请使用 business-logic-verify 对以下本地授权项目做业务逻辑漏洞动态验证。
项目路径：<local path>
授权边界：仅限本地测试环境
启动方式：<command>
测试数据库或快照：<db/fixture/snapshot>
测试账号与角色：<role matrix>
测试租户：<tenant A/B>
日志位置：<app/worker/queue logs>
禁止项：不访问公网或敏感内网；不调用真实支付；不破坏真实数据；不做 DoS 或压测
```

## 交付验收

- 目录只包含 1 个主 Skill。
- 名称使用小写英文短横线，并能看出“业务逻辑验证”主题。
- 所有文件非空，且均能追溯到 TXT 原文或工程化补强理由。
- `SKILL.md` 包含适用范围、不适用范围、输入要求、输出要求、原文复刻规则、工程化补强规则、核心工作流、分阶段执行步骤、质量门禁、幻觉控制、失败处理、输出格式、自检清单、TXT 到 Skill 映射说明。
- 模板有可填写字段，不是标题占位。
- checklist 是可勾选格式，并能阻止无动态证据的 `confirmed`。
- examples 贴近本地授权业务逻辑验证场景。
- tests 能检查漏复刻、摘要化、无关扩展、命名失败、目录臃肿、输入输出缺失、质量门禁缺失、失败处理缺失、TXT 映射缺失、工程化补强伪装原文。

## Windows PowerShell 落地命令

```powershell
$Zip = ".\business-logic-verify-reviewed.zip"
$Dest = ".\claude-skills"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
Expand-Archive -Path $Zip -DestinationPath $Dest -Force
Get-ChildItem -Recurse "$Dest\business-logic-verify" | Select-Object FullName, Length
Test-Path "$Dest\business-logic-verify\SKILL.md"
Test-Path "$Dest\business-logic-verify\templates\output-template.md"
Test-Path "$Dest\business-logic-verify\checklists\quality-gate.md"
Test-Path "$Dest\business-logic-verify\checklists\final-review.md"
Test-Path "$Dest\business-logic-verify\examples\basic-example.md"
Test-Path "$Dest\business-logic-verify\examples\full-example.md"
Test-Path "$Dest\business-logic-verify\tests\skill-quality-tests.md"
```

## 安全说明

本包只包含 Markdown 文件，不包含 `.ps1`、`.sh`、`.bat`、`.cmd`、`.exe`、二进制文件、依赖包或联网脚本。
