# ssrf-canary-audit

## 用途

本 Skill 把 `SSRF提示词转Skills.txt` 复刻为一个可调用、可落地、可验收、可追溯的 Claude Skill。它用于本地授权开源项目的 SSRF 动态验证审计，核心判定是：没有服务端到本地 canary 的真实回连证据，不得 confirmed；没有 canary 回连，不得高危；没有复现步骤，不得输出漏洞结论。

## Skill 数量

只保留 1 个主 Skill。TXT 的三段内容分别是 SSRF 动态验证、结果反向审判、最终追责审计，三者共享同一输入、同一证据目录、同一状态体系和同一最终报告，不应拆成多个 Skill。

## 目录

```text
ssrf-canary-audit/
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

## 使用前提

必须具备：本地授权项目路径、本地应用启动方式、本地应用地址、本地 canary 地址、证据目录、测试账号或不适用说明、应用日志采集方式。没有授权边界或没有 canary 时，不得执行动态验证。

## 调用示例

```text
请使用 ssrf-canary-audit Skill，对当前本地授权项目执行 SSRF 动态验证审计。
project_root: C:\lab\demo-app
app_start_command: npm run dev
app_base_url: http://127.0.0.1:3000
canary_base_url: http://127.0.0.1:7777
evidence_dir: evidence/ssrf/
authorization_scope: 仅当前本地授权项目、本机 canary、测试容器网络、测试目录 marker 服务。
prohibited_targets: 真实公网敏感地址、云 metadata、真实内网资产、公司内网、第三方服务、生产服务。
```

## 执行顺序

1. 按 `SKILL.md` 确认边界和输入。
2. 建立本地应用与本地 canary。
3. 建立 SSRF 暴露面矩阵。
4. 对每个 candidate 构造唯一 marker 并动态验证。
5. 保存 canary 日志、应用日志、请求样本、响应样本、代码调用链、正例、反例、blocked case、复现步骤和回归测试。
6. 使用 `checklists/quality-gate.md`、`checklists/final-review.md` 和 `tests/skill-quality-tests.md` 交付前审查。
7. 最终报告按 `templates/output-template.md` 输出。

## 验收标准

1. 只有 1 个主 Skill。
2. 没有空壳目录或空壳文件。
3. 原文复刻和工程化补强被明确区分。
4. confirmed 只保留有 canary、应用日志、请求样本、代码链、正例、反例、blocked case、复现步骤、回归测试同时支撑的结论。
5. candidate、blocked、needs_review 不被夸大。
6. 所有动态验证只指向本地 canary 或本地测试网络。
7. 最终报告能从结论追溯到 TXT 要求和 `evidence/ssrf/` 证据。
