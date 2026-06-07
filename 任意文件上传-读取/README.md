# File Boundary Verify

## 作用

`file-boundary-verify` 是把“本地授权项目文件处理安全动态验证”TXT 转成的 Claude Skill。它约束 Claude 不做泛泛静态审计，而是围绕 marker 文件、真实请求、文件系统前后状态、权限/租户矩阵和反向审判来验证文件上传、读取、写入、路径边界、压缩包解压、对象存储 key 映射和二次访问链路。

## Skill 数量决策

最终只保留 1 个主 Skill。TXT 前半部分是动态验证流程，后半部分是对同一批结论的反向审判。二者输入相同，输出同一份报告，拆分会产生重复和调用成本。

## 目录结构

```text
file-boundary-verify/
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

## 使用输入

```yaml
project_root: "<本地授权项目路径>"
local_base_url: "http://127.0.0.1:<port>"
auth_contexts:
  anonymous: "无登录态"
  user_a: "普通用户 A 测试态"
  user_b: "普通用户 B 测试态"
  admin: "管理员测试态"
  readonly: "只读角色测试态"
tenant_contexts:
  - tenant_a
  - tenant_b
test_marker_root: "<project_root>/security-markers/file-boundary-{uuid}"
evidence_output_dir: "<project_root>/security-evidence/file-boundary-{uuid}"
allowed_operations:
  - upload
  - download
  - preview
  - read-marker
  - write-marker
  - import
  - export
  - archive-extract
  - object-key-map
rollback_policy: "删除 marker 目录、测试上传记录、导入任务、导出缓存"
```

## Windows PowerShell 落地命令

```powershell
$ZipPath = "C:\Users\$env:USERNAME\Downloads\file-boundary-verify-reviewed.zip"
$TargetDir = "C:\Users\$env:USERNAME\ClaudeSkills"
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
Expand-Archive -Path $ZipPath -DestinationPath $TargetDir -Force

$SkillDir = Join-Path $TargetDir "file-boundary-verify"
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
foreach ($Item in $Required) {
  $Path = Join-Path $SkillDir $Item
  if (-not (Test-Path $Path)) { throw "Missing required file: $Item" }
}
Write-Host "file-boundary-verify is complete."
```

## TXT 复刻一致性映射表

| TXT 原文位置/标题 | 原文关键内容 | Skill 位置 | 复刻类型 |
|---|---|---|---|
| 角色设定 | 文件处理安全动态验证负责人 | SKILL.md 适用范围 | 原文复刻 |
| 目标 | 上传、写入、路径穿越、危险解析、读取、下载绕过、预览读取、导入导出、解压写入、对象 key 映射 | SKILL.md 适用范围、原文复刻规则 | 原文复刻 |
| 重要边界 1-10 | 授权、本地、禁止敏感读取、marker、无害上传、禁止 DoS、MITM 排除、confirmed 证据 | SKILL.md 不适用范围、原文复刻规则、质量门禁 | 原文复刻 |
| 先理解项目 | 语言、框架、路由、上传中间件、存储、对象存储、下载、预览、导入导出、管理、附件、头像、模板、插件、主题、日志、报表 | SKILL.md 阶段 2、quality-gate.md | 原文复刻 |
| 文件依赖识别 | multipart、图片、PDF、Office、压缩包、对象存储 SDK、路径库、模板、静态资源、反序列化导入 | SKILL.md 阶段 8、quality-gate.md | 原文复刻 |
| 文件流转图 | 入口参数到删除链路 | SKILL.md 阶段 2、output-template.md 第 4 节 | 原文复刻 |
| 用户可控字段 | filename、path、key、url 等完整字段清单 | SKILL.md 原文复刻规则、quality-gate.md | 原文复刻 |
| 隐藏参数 | multipart、JSON、query、header、GraphQL、WebSocket | SKILL.md 阶段 2、阶段 4、阶段 5 | 原文复刻 |
| 安全测试环境 | marker 根目录、allowed、blocked、upload、download、before/after、回滚 | SKILL.md 阶段 3、quality-gate.md、output-template.md | 原文复刻 |
| 上传入口验证 | 14 类上传验证和每项证据字段 | SKILL.md 阶段 4、quality-gate.md、output-template.md | 原文复刻 |
| 读取入口验证 | 14 类读取入口和 8 类请求构造 | SKILL.md 阶段 5、quality-gate.md | 原文复刻 |
| 路径规范化与边界验证 | join/resolve/normalize、编码、软链接、对象 key、系统差异、解压、二次读取 | SKILL.md 阶段 6、quality-gate.md | 原文复刻 |
| 角色、租户、权限矩阵 | 未登录、用户 A/B、租户、管理员、只读、低权限、拥有者/非拥有者 | SKILL.md 阶段 7、output-template.md | 原文复刻 |
| 依赖与框架专项 | Node、Python、Java、PHP、Go、Ruby 文件处理对象 | SKILL.md 阶段 8 | 原文复刻 |
| 证据要求 | evidence manifest 字段 | SKILL.md 阶段 9、output-template.md 第 8/16 节 | 原文复刻 + 工程化补强 |
| 严禁 1-10 | 无请求不得 confirmed、无 marker 不得任意读取、403/404 不等于安全、不得忽略 worker/对象存储/二次链路 | SKILL.md 幻觉控制、quality-gate.md | 原文复刻 |
| 最终输出格式 | 14 项报告结构 | SKILL.md 输出要求、output-template.md | 原文复刻 |
| 反向审判模式 | 审判结论、遗漏入口、偏门上传、偏门读取、依赖风险、代码结构、矩阵、降级、最终交付 | checklists/final-review.md、SKILL.md 阶段 10 | 原文复刻 |
| 验证编号、状态枚举、矩阵格式、PowerShell 落地 | 让 Skill 可执行、可验收、可落地 | SKILL.md 工程化补强规则、README.md、tests | 工程化补强 |

## 交付边界

本 Skill 不保证发现漏洞。它保证结论分级受证据约束：没有动态证据不得 confirmed，读取/写入只允许 marker，所有未覆盖项必须列出原因和下一步补测动作。
