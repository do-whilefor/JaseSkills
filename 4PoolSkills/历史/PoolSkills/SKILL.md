---
name: PoolSkills
description: 本机授权安全审计 Skills 总入口。用于用户明确授权的项目、靶场、开源测试项目与 Skills 包自检；输出必须区分 candidate、needs_review、inconclusive、confirmed，禁止把未验证候选写成确认漏洞。
---

# Authorized Security Audit System

## 触发边界

仅在用户明确要求审查授权目标测试项目或本 Skills 包时触发。不得对未授权第三方目标执行扫描、爆破、绕过、持久化、破坏性写入或真实数据获取。

## 执行原则

默认做非破坏性本机验证。任何可能修改真实数据、触发外部系统、越出授权范围的验证都必须标为 `UNSAFE_TO_TEST` 或 `needs_review`。

对目标项目执行前必须加载目标仓库的 `scope.yaml`，或使用目标根目录为边界的默认 scope。没有 schema、evidence manifest、动态证据、负向控制或必要角色/租户矩阵时，不得将严重漏洞写为 confirmed。

## 推荐执行链

1. 运行 `tools/runtime_check.py` 或 `scripts/windows_preflight.py` 检查 Python、Node、Playwright、parser 与本机依赖。
2. 运行 `run_engine_selftest.py` 验证 collectors、analyzers、detectors、dynamic、evidence、quality、report 的基本链路。
3. 对授权目标运行 collectors 与 analyzers，生成 route、JS、参数、图谱和 taint 结果。
4. 运行 detector，仅生成 candidate 或 needs_review。
5. 生成 replay plan，并在授权测试环境内做非破坏性动态验证。
6. 将动态 artifacts stitch 到 evidence manifest。
7. 运行 `quality/quality_gate.py`，只接受门禁允许的 confirmed 状态。
8. 使用 `report/report_generator.py` 生成报告。

## 证据约束

严重风险进入 confirmed 必须同时满足：schema-valid candidate、schema-valid evidence manifest、schema-valid replay result、可读脱敏证据、manifest-backed request/response/screenshot-or-DOM、replay success、负向控制、阻断控制记录、严重风险跨文件 source-sink dataflow，以及需要时的非占位 role/tenant。

不得把 dashboard、AI 文本、人工描述或原始工具输出直接作为漏洞证据；必须转换成 schema-valid、已脱敏、可读且位于 manifest root 内的 evidence manifest 条目。

## Windows 使用

Windows 入口位于 `windows/run_skills.ps1` 和 `windows/run_skills.cmd`。入口脚本支持带空格路径，优先使用目标仓库 `scope.yaml`；目标没有 scope 时使用内存默认 scope，不向目标仓库写入配置。显式指定 scope 时使用 `-ScopeFile`。

## 知识库与模板

保留并优先复用以下目录：`knowledge/`、`raw_original_kb_templates/`、`vulnerability_templates/`、`vulnerability_research_units/`、`report_templates/`、`rules/`。
