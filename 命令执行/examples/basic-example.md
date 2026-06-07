# basic-example

## 调用示例

```text
使用 cmd-exec-risk-replay Skill。
项目路径：C:\work\demo-app
授权范围：仅限 C:\work\demo-app 的本地测试环境。
测试目录：./security-lab/
marker 目录：./security-lab/markers/
证据目录：./security-lab/evidence/
角色/租户：user/admin，tenant-a/tenant-b。
输出：使用 templates/output-template.md；没有动态证据不得 confirmed。
```

## 最小合格输出片段

```markdown
## 边界确认

| 边界项 | 结论 | 证据/说明 |
|---|---|---|
| 仅当前本地授权项目 | yes | project_root 为 C:\work\demo-app |
| marker 目录 | yes | ./security-lab/markers/ 可写 |

## replay plan 清单

### CMD-EXEC-20260607-001

| 字段 | 内容 |
|---|---|
| 入口点 | 本地测试环境中的文件导入功能 |
| 权限前提 | 普通测试用户，tenant-a |
| 数据流 | multipart 文件名 → 导入参数归一化 → 外部转换工具 wrapper |
| 无害 marker | MARKER-CMD-EXEC-20260607-001 |
| 正向验证 | 写入 marker_dir 或记录受控 stdout/stderr |
| 负向验证 | 正常文件名、转义文件名、低权限角色、tenant-b |
| 初始结论等级 | candidate |
```

## 不合格输出片段

```markdown
发现命令执行漏洞，风险较高。攻击者可能执行系统命令。
```

不合格原因：没有 source、sink、replay plan、marker 证据、负向验证、代码位置、结论等级依据。
