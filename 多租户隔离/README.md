# tenant-isolation-dynamic-validation

## 用途

本 Claude Skill 将 `提示词转skills.txt` 中的“本地授权开源项目租户隔离漏洞动态验证专家/反向审判模式”落成可调用流程。它要求 Claude 在本地或授权环境内建立事实画像、租户矩阵、marker 资源、暴露面表、动态请求证据、confirmed/candidate 分流、同族拓展和第二轮反向审判。

## 文件结构

```text
tenant-isolation-dynamic-validation/
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

## 文件作用

| 文件 | 作用 |
|---|---|
| `SKILL.md` | Claude 调用时的核心规则和 TXT 映射 |
| `templates/output-template.md` | 最终审计报告固定模板 |
| `checklists/quality-gate.md` | 交付前质量门禁 |
| `checklists/final-review.md` | 第二轮反向审判和覆盖盲区复核 |
| `examples/basic-example.md` | 最小调用示例 |
| `examples/full-example.md` | 完整报告骨架示例 |
| `tests/skill-quality-tests.md` | 检测摘要化、空壳化、误报、漏项的测试 |

## 调用示例

```text
使用 tenant-isolation-dynamic-validation Skill。
项目路径：C:\labs\local-saas
API 地址：http://127.0.0.1:3000
测试数据库：本地 docker postgres，测试库 local_saas_test
测试账号：A_owner/A_admin/A_member/A_viewer/B_owner/B_admin/B_member/B_viewer，凭证已脱敏
限制：只能使用 marker 数据，不允许删除真实业务数据
输出：完整租户隔离动态验证报告和第二轮反向审判复核
```

## Windows PowerShell 落地命令

```powershell
$SkillRoot = ".\tenant-isolation-dynamic-validation"
New-Item -ItemType Directory -Force -Path $SkillRoot | Out-Null
New-Item -ItemType Directory -Force -Path "$SkillRoot\templates" | Out-Null
New-Item -ItemType Directory -Force -Path "$SkillRoot\checklists" | Out-Null
New-Item -ItemType Directory -Force -Path "$SkillRoot\examples" | Out-Null
New-Item -ItemType Directory -Force -Path "$SkillRoot\tests" | Out-Null

@'
<粘贴 SKILL.md 完整内容>
'@ | Set-Content -Encoding UTF8 "$SkillRoot\SKILL.md"

@'
<粘贴 README.md 完整内容>
'@ | Set-Content -Encoding UTF8 "$SkillRoot\README.md"

@'
<粘贴 templates/output-template.md 完整内容>
'@ | Set-Content -Encoding UTF8 "$SkillRoot\templates\output-template.md"

@'
<粘贴 checklists/quality-gate.md 完整内容>
'@ | Set-Content -Encoding UTF8 "$SkillRoot\checklists\quality-gate.md"

@'
<粘贴 checklists/final-review.md 完整内容>
'@ | Set-Content -Encoding UTF8 "$SkillRoot\checklists\final-review.md"

@'
<粘贴 examples/basic-example.md 完整内容>
'@ | Set-Content -Encoding UTF8 "$SkillRoot\examples\basic-example.md"

@'
<粘贴 examples/full-example.md 完整内容>
'@ | Set-Content -Encoding UTF8 "$SkillRoot\examples\full-example.md"

@'
<粘贴 tests/skill-quality-tests.md 完整内容>
'@ | Set-Content -Encoding UTF8 "$SkillRoot\tests\skill-quality-tests.md"

Get-ChildItem -Recurse $SkillRoot | Select-Object FullName, Length
Compress-Archive -Path $SkillRoot -DestinationPath ".\tenant-isolation-dynamic-validation.zip" -Force
```

## 验收标准

合格输出必须能回答：读了哪个 TXT；TXT 规则映射到哪个文件；哪些内容是工程化补强；是否保留 1 个主 Skill；是否无空壳文件；是否有模板、清单、示例、测试；confirmed 是否有动态证据；candidate 是否未被伪装；第二轮反向审判是否执行。
