# Local Injection Verify

`local-injection-verify` 是从 `注入类提示词转skills.txt` 复刻出的单主 Claude Skill。它把原 TXT 的“授权本地项目注入类缺陷动态验证负责人”和“注入类漏洞反向审判官”合并为同一条工作链：先建立本地授权项目的注入暴露面和动态验证证据，再反向审判所有 confirmed/high/critical 结论。

## Skill 数量

只保留 1 个主 Skill。原 TXT 的两段角色共享同一输入、同一证据链、同一输出报告和同一降级规则；拆成多个 Skill 会造成矩阵、计划、证据、结论和反查结果分散。

## 目录

```text
local-injection-verify/
  SKILL.md
  README.md
  templates/output-template.md
  checklists/quality-gate.md
  checklists/final-review.md
  examples/basic-example.md
  examples/full-example.md
  tests/skill-quality-tests.md
  source/original-txt.txt
  mappings/txt-skill-map.md
```

`source/` 保存原 TXT。`mappings/` 保存 TXT 到 Skill 映射。没有 `manifest.json`、脚本、空目录或装饰性目录。

## 调用输入

```text
使用 local-injection-verify。
项目路径：<本地授权项目路径>
启动命令或本地服务地址：<命令或 http://127.0.0.1:port>
测试数据库/回滚方式：<测试库和重置方式>
测试账号/角色/租户矩阵：<账号、角色、租户>
日志位置：<日志路径或日志命令>
允许写入的测试目录：<测试目录>
CLI/队列/任务/导入导出触发方式：<可用触发命令或 blocked>
目标：输出反查修正版注入类缺陷报告。没有动态证据不得 confirmed。
```

## 输出

默认输出 `templates/output-template.md` 中的完整报告。所有 confirmed 必须能追溯到矩阵编号、计划编号、结果编号和证据编号。证据不足时必须降级为 `candidate`、`blocked` 或 `needs manual review`。

## Windows PowerShell 落地命令

```powershell
$SkillRoot = ".\local-injection-verify"
New-Item -ItemType Directory -Force $SkillRoot | Out-Null
New-Item -ItemType Directory -Force "$SkillRoot\templates" | Out-Null
New-Item -ItemType Directory -Force "$SkillRoot\checklists" | Out-Null
New-Item -ItemType Directory -Force "$SkillRoot\examples" | Out-Null
New-Item -ItemType Directory -Force "$SkillRoot\tests" | Out-Null
New-Item -ItemType Directory -Force "$SkillRoot\source" | Out-Null
New-Item -ItemType Directory -Force "$SkillRoot\mappings" | Out-Null
# 将压缩包中的 local-injection-verify 文件夹内容复制到上述目录。
```

压缩包不包含 `.ps1`、`.sh`、`.bat`、`.cmd`、`.exe`。
