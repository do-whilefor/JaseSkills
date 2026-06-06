# 极限 JS Skills 评审知识清单

本文件把用户粘贴的评审要求固化为可检索知识。评审时必须同时检查文档、脚本、schema、模板、tests、fixtures、knowledge、dashboard 和命令输出。

## 不可虚高原则

- regex/grep/keyword 只能算候选提取，不得称为 AST 级审计。
- 静态发现只能是 candidate，不得称为 verified。
- Playwright/Burp/HAR/tree-sitter/Babel/TypeScript Compiler API 只要没有 runtime availability check、调用脚本、测试样本和证据输出，就不能标 ready。
- 知识库文件存在不等于知识库已接入；必须有索引、触发条件、冲突处理、引用路径。
- 模板存在不等于检测器存在；必须绑定 evidence manifest、quality gate、report section。

## 评审必查目录

`SKILL.md`、`CLAUDE.md`、`README.md`、`docs/`、`scripts/`、`tools/`、`bin/`、`lib/`、`src/`、`tests/`、`fixtures/`、`schemas/`、`templates/`、`knowledge/`、`reports/`、`dashboard/`。

## 必查证据

每个结论必须绑定文件路径、脚本名、函数名、schema 字段、模板名、测试用例名、fixture 名、dashboard 字段、manifest 字段或命令输出。缺证据时写“未证实”。
