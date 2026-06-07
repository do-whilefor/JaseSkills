# Skill 质量测试

本文件用于验收 `business-logic-verify` 是否真正复刻 `业务逻辑转skills.txt`，并检测摘要化、幻觉扩展、空壳文件、命名失败和工程化补强伪装原文。

## 1. 必备文件测试

- [ ] 存在 `SKILL.md`。
- [ ] 存在 `README.md`。
- [ ] 存在 `templates/output-template.md`。
- [ ] 存在 `checklists/quality-gate.md`。
- [ ] 存在 `checklists/final-review.md`。
- [ ] 存在 `examples/basic-example.md`。
- [ ] 存在 `examples/full-example.md`。
- [ ] 存在 `tests/skill-quality-tests.md`。
- [ ] 不存在空文件。
- [ ] 不存在 `rules/`、`workflows/`、`schemas/`、`fixtures/` 等无理由目录。

## 2. TXT 关键内容覆盖测试

- [ ] `SKILL.md` 覆盖“本地授权开源项目”。
- [ ] `SKILL.md` 覆盖“业务逻辑漏洞动态验证”。
- [ ] `SKILL.md` 覆盖不分析中间人攻击、网络劫持、证书绕过、流量篡改。
- [ ] `SKILL.md` 覆盖测试环境、测试数据库、测试账号、测试租户、测试 webhook。
- [ ] `SKILL.md` 覆盖禁止破坏数据库、删除真实数据、影响真实业务。
- [ ] `SKILL.md` 覆盖禁止 DoS、DDoS、资源耗尽、批量压测、恶意刷接口。
- [ ] `SKILL.md` 覆盖禁止公网敏感地址、内网敏感地址、云元数据地址、第三方系统。
- [ ] `SKILL.md` 覆盖 candidate 不得伪装 confirmed。
- [ ] `SKILL.md` 覆盖不允许编造请求、响应、日志、截图、数据库记录或执行结果。
- [ ] `SKILL.md` 覆盖项目理解阶段：语言、框架、入口、路由、控制器、service、model、middleware、worker、队列、定时任务。
- [ ] `SKILL.md` 覆盖认证方式：session、JWT、OAuth、API key、magic link、邮箱验证码、手机验证码、webhook signature、admin token、service token。
- [ ] `SKILL.md` 覆盖权限模型、业务对象、状态机、业务流程图。
- [ ] `SKILL.md` 覆盖 10 类业务逻辑漏洞方向。
- [ ] `SKILL.md` 覆盖 replay plan 11 项字段。
- [ ] `SKILL.md` 覆盖 confirmed 证据要求。
- [ ] `SKILL.md` 覆盖最终报告结构、工程级修复建议、第一轮反思、第二轮补挖、最终硬性要求。
- [ ] `checklists/final-review.md` 覆盖 confirmed 20 项复核。

## 3. 防摘要化测试

出现以下任一情况即失败：

- [ ] 只写“检查业务逻辑漏洞”，没有列出 10 类验证方向。
- [ ] 只写“收集证据”，没有列出请求、响应、DB 前后、日志、代码位置、负向验证。
- [ ] 只写“做复核”，没有列出第一轮 15 项反思和第二轮 15 项偏门补挖。
- [ ] 只写“输出报告”，没有给出可填写字段。
- [ ] 只写“验证权限”，没有覆盖状态机、金额、幂等、并发、webhook、账号生命周期、隐藏参数、多租户、业务不变量。

## 4. 无关扩展测试

- [ ] Skill 没有加入公网目标验证。
- [ ] Skill 没有加入第三方攻击流程。
- [ ] Skill 没有加入 MITM、证书绕过、流量篡改。
- [ ] Skill 没有加入大规模压测或资源耗尽。
- [ ] Skill 没有声称自动攻击真实支付、真实用户、真实租户或第三方系统。
- [ ] Skill 没有把证据编号、报告元数据、PowerShell 检查命令等工程化补强写成 TXT 原文。

## 5. 命名测试

- [ ] Skill 目录名是 `business-logic-verify`。
- [ ] 名称为小写英文短横线。
- [ ] 名称能看出核心主题是业务逻辑验证。
- [ ] 名称不包含 best、final、new、advanced、ultimate、audit-skill、skill-only。
- [ ] 文件名简短，并能看出文件作用。
- [ ] 不存在 `README-final.md`、`new-template.md`、`copy.md`。

## 6. 目录结构测试

- [ ] 目录只包含 `SKILL.md`、`README.md`、`templates/`、`checklists/`、`examples/`、`tests/`。
- [ ] `templates/` 只包含 `output-template.md`。
- [ ] `checklists/` 只包含 `quality-gate.md` 和 `final-review.md`。
- [ ] `examples/` 只包含 `basic-example.md` 和 `full-example.md`。
- [ ] `tests/` 只包含 `skill-quality-tests.md`。

## 7. 输入输出定义测试

- [ ] `SKILL.md` 明确输入要求。
- [ ] `SKILL.md` 明确输出要求。
- [ ] `templates/output-template.md` 给出最终报告字段。
- [ ] 输出分级包含 `confirmed`、`candidate`、`blocked`、`false_positive`、`needs_environment`。
- [ ] `confirmed` 字段包含动态证据和负向验证。
- [ ] 失败处理包含未授权、无测试库、服务无法启动、缺少角色/租户、只有代码可疑点、被后端机制阻断、误判场景。

## 8. 质量门禁测试

- [ ] `SKILL.md` 有质量门禁。
- [ ] `checklists/quality-gate.md` 有可勾选门禁。
- [ ] 门禁能阻止无授权、无测试数据、无动态证据、无 DB 前后、无日志的问题进入 `confirmed`。
- [ ] 门禁能处理 `blocked`、`false_positive`、`needs_environment`。
- [ ] 门禁包含“未建立映射表不得通过”。
- [ ] 门禁包含“未区分原文复刻和工程化补强不得通过”。

## 9. TXT 映射测试

- [ ] `SKILL.md` 含 TXT 到 Skill 映射说明。
- [ ] 映射覆盖开头角色与任务。
- [ ] 映射覆盖强制边界。
- [ ] 映射覆盖项目理解阶段。
- [ ] 映射覆盖 10 类业务逻辑漏洞方向。
- [ ] 映射覆盖动态验证标准。
- [ ] 映射覆盖证据要求。
- [ ] 映射覆盖输出格式。
- [ ] 映射覆盖第一轮强制反思。
- [ ] 映射覆盖第二轮偏门补挖。
- [ ] 映射覆盖最终硬性要求和 confirmed 20 项审判。
- [ ] 映射表标明“原文复刻”或“工程化补强”。

## 10. PowerShell 本地检查命令

```powershell
$Root = ".\business-logic-verify"
$Required = @(
  "SKILL.md",
  "README.md",
  "templates\output-template.md",
  "checklists\quality-gate.md",
  "checklists\final-review.md",
  "examples\basic-example.md",
  "examples\full-example.md",
  "tests\skill-quality-tests.md"
)
foreach ($File in $Required) {
  $Path = Join-Path $Root $File
  if (!(Test-Path $Path)) { throw "Missing $File" }
  if ((Get-Item $Path).Length -eq 0) { throw "Empty $File" }
}
$AllFiles = Get-ChildItem -Recurse $Root -File | ForEach-Object { $_.FullName.Replace((Resolve-Path $Root).Path + "\", "") }
foreach ($File in $AllFiles) {
  if ($Required -notcontains $File) { throw "Unexpected file $File" }
}
```

## 11. 失败判定

任一测试项失败，Skill 不得交付。失败项必须直接修复到对应文件，不得只记录为后续事项。
