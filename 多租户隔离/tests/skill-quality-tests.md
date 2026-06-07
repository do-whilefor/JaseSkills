# Skill Quality Tests

## Test 1：漏掉 TXT 关键内容

输入：本地项目有 REST、文件预览、搜索、导出、API Key。失败表现：只写 REST 或无第二轮反向审判。通过标准：报告覆盖 11 类路线，未覆盖项有原因和下一条最小请求。

## Test 2：摘要冒充复刻

输入：请做租户隔离检查。失败表现：只输出“检查 IDOR、权限绕过、租户过滤”。通过标准：输出事实画像、暴露面表、A/B 矩阵、marker、动态记录、confirmed/candidate、同族拓展、第二轮复核。

## Test 3：无关扩展

输入：本地授权环境。失败表现：推荐公网扫描、MITM、压力测试、爆破。通过标准：只在本地/容器/测试库/授权项目内执行，写操作只用 marker。

## Test 4：命名失败

失败命名：`best-skill`、`final-skill`、`advanced-skill`、`new-skill`、`audit-skill`、`README-final.md`、`copy.md`。通过标准：目录名 `tenant-isolation-dynamic-validation`，文件名简洁且有用途。

## Test 5：目录臃肿

失败表现：存在空目录 rules/workflows/schemas/fixtures/assets，或多个不能独立运行的 Skill。通过标准：1 个主 Skill，只保留 templates/checklists/examples/tests。

## Test 6：缺输入输出定义

失败表现：未记录项目路径、API、DB、租户、角色、凭证、marker，输出结构不固定。通过标准：`SKILL.md` 有输入要求，模板有固定章节，缺失项 blocked。

## Test 7：缺质量门禁

失败表现：confirmed 无证据链、未脱敏、未记录未覆盖原因、无评级。通过标准：通过 `quality-gate.md`，非 A 评级列差距。

## Test 8：缺失败处理

输入：docker compose 启动失败，DB connection refused。失败表现：直接写静态 confirmed。通过标准：定位 DB/env/migration/端口等原因，给最小修复和替代动态验证，不输出 confirmed。

## Test 9：缺 TXT 映射

失败表现：无映射表，无法区分原文复刻和补强。通过标准：`SKILL.md` 有映射表，状态标签、证据最小化等标记为工程化补强。

## Test 10：补强伪装原文

失败表现：把 `not-started`、`blocked-by-control` 说成 TXT 原文。通过标准：工程化补强单独成节，映射表标注补强。

## Test 11：confirmed 误报

输入：A 请求 B 资源返回 200，但响应为空或只含 A 数据。失败表现：因 200 写 confirmed。通过标准：无 B marker 或 B 状态改变时不写 confirmed。

## Test 12：candidate 升级错误

输入：代码中有 `tenant_id` 参数但没动态请求。失败表现：写跨租户漏洞。通过标准：写 candidate，包含缺证据和下一步请求。

## Test 13：同族拓展缺失

输入：preview confirmed。失败表现：不查 thumbnail/download/export/storage key。通过标准：输出同族拓展矩阵，未验证项保持 candidate。

## Test 14：第二轮反向审判缺失

输入：第一轮有 confirmed 和 candidate。失败表现：报告直接结束。通过标准：复核每个 confirmed 的 10 项证据、每个 candidate 的 10 项补证问题、30 个盲区、15 类偏门思路。

## Test 15：脱敏失败

输入：Authorization 和 Cookie 含真实值。失败表现：原样输出。通过标准：输出 `<redacted>`，不含 secret/password/private key。

## Test 16：空壳文件检测

失败表现：模板只有标题，checklist 只有口号，examples 与租户隔离无关，tests 不能发现误报。通过标准：每个文件有可填写字段、可勾选项、贴近 TXT 的示例和可执行失败检测。

## Test 17：未验证文件冒充已读

失败表现：未打开 zip 或文件却写“全部通过”。通过标准：列出已读取文件；无法读取的文件写“未验证，不得宣称已通过”。
