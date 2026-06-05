# 本机授权安全审计系统

本目录是一个单一可安装 Claude Skill。`skills/` 下的目录是内部路由模块，必须与 `_shared/`、`schemas/`、`tools/`、`tests/`、`reports/`、`dashboard/` 一起保留。

## 保留范围

- 主体 Skill 入口：`SKILL.md`、`CLAUDE.md`、`skills/`。
- 知识库与索引：`_shared/knowledge/`、`_shared/knowledge_index.json`。
- 漏洞模板与 23 类严重漏洞规则：`_shared/vulnerability_templates/`、`_shared/vulnerability_research_units/`、`skills/07-vulnerability-hunting-engine/`。
- 证据、质量门、replay、dashboard、report template、schema 与本机自检工具。

## 使用边界

仅用于本机授权源码、本机靶场、本机 fixture、本机 replay 和用户明确授权的测试项目。禁止用于未授权第三方目标，禁止破坏性写入、拒绝服务、凭证滥用、隐蔽持久化、横向移动或真实数据窃取。

## 安装

PowerShell：

```powershell
Copy-Item -Recurse .uthorized_security_audit_system $env:USERPROFILE\.claude\skillsuthorized_security_audit_system -Force
```

Bash：

```bash
mkdir -p ~/.claude/skills
cp -R authorized_security_audit_system ~/.claude/skills/authorized_security_audit_system
```

## 验证

从包根目录执行：

```bash
python3 tools/runtime_check.py --out /tmp/runtime_readiness.json
python3 tools/selftest.py --out /tmp/selftest_result.json
python3 _shared/tests/adversarial_test_harness.py
python3 _shared/tests/e2e_replay/e2e_replay_runner.py
python3 _shared/tests/high_risk_replay/high_risk_replay_runner.py
```

浏览器、代理、语言 parser 或真实 OSS checkout 缺失时，只能声明对应能力为未就绪或候选能力，不得声称动态确认或完整语义审计。

## 关键入口

- `SKILL.md`
- `CLAUDE.md`
- `CAPABILITY_MATRIX.md`
- `SECURITY_AUDIT_WORKFLOW.md`
- `REVIEW_QUEUE.md`
- `INSTALL_AND_VERIFY.md`
- `tools/runtime_check.py`
- `tools/selftest.py`
- `reports/templates/finding_template.md`
- `dashboard/index.html`
