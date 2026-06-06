# SecKB Claude Skills v2 Audited

本版本是对上一版 Skills 的攻击性审计补强版。它保留原始文档能力，并新增能力索引、质量门禁、失败案例库、反幻觉策略、维护说明和自测脚本。新增内容均属于**基于文档延伸**，不伪装成原文档内容。

## 使用前必须区分两个目录

- Claude Skills 安装目录：`%USERPROFILE%\.claude\skills\seckb-claude-skills-audited-v2`
- SecKB 知识库目录：`D:\Users\21452\AppData\SecKB`

Skills 是执行规则和模板；SecKB 是被构建和维护的知识库。不要混用。

## 优先读取顺序

1. `CAPABILITY_INDEX.md`
2. `01-seckb-master-orchestrator/SKILL.md`
3. `docs/quality-gate-policy.md`
4. 目标子 Skill
5. 对应模板或脚本

---

# SecKB Claude Skills Complete

这套 Skills 用于构建、维护、检索、验证和反向审计本地安全知识库 SecKB。

默认知识库根目录：

```text
D:\Users\21452\AppData\SecKB
```

## 设计目标

1. 一比一保留源文档中的有效流程、规则、边界、模板、质量门槛和输出结构。
2. 让 Claude 先读索引再读细节，减少 RAG 查错、模板误用和工具告警误判。
3. 将公开漏洞、SRC 规则、工具 release、代码审计知识、漏洞模板、动态验证证据统一沉淀到 SecKB。
4. 将所有不确定内容默认放入 `needs_review`，只有通过质量门槛才允许进入 `promoted`。
5. 动态验证只允许在本机、靶场、本地开源项目或明确授权范围内进行。
6. 0day-class 学习仅保留防御性研究、补丁差分、根因模式、代码审计切入点和负责任披露流程。

## Skills 列表

1. `01-seckb-master-orchestrator`：总控入口、任务识别、安全边界和子 Skill 路由。
2. `02-source-collection-freshness`：公开来源采集、近 30 天 freshness、历史高价值补充。
3. `03-normalize-index-rag-router`：统一 schema、去重、可信度评分、索引构建、RAG 路由测试。
4. `04-vuln-template-factory`：漏洞模板生成、保真度检查、误报与不可报告原因。
5. `05-code-audit-knowledge`：语言/框架级代码审计知识沉淀。
6. `06-src-rules-compliance`：SRC/众测/应急响应中心官方规则与合规边界。
7. `07-toolchain-release-learning`：安全工具 README/release/规则变化与本地联动。
8. `08-dynamic-validation-evidence`：授权动态验证、证据 manifest 和可报告性判断。
9. `09-variant-learning-patch-diff`：补丁差分、silent fix、防御性变体学习。
10. `10-audit-quality-regression`：反向审计、降级/归档、负样本测试、人工确认和 dashboard。

## 安装位置

Windows Claude Skills 可放入：

```powershell
$skillsRoot = "$env:USERPROFILE\.claude\skills"
Expand-Archive -Path .\seckb-claude-skills-complete.zip -DestinationPath $skillsRoot -Force
```

安装后目录应类似：

```text
%USERPROFILE%\.claude\skills\seckb-claude-skills-complete\01-seckb-master-orchestrator\SKILL.md
```

## 使用入口

优先用以下任务触发总控：

```text
请调用 SecKB Skills，读取 D:\Users\21452\AppData\SecKB\CLAUDE.md 和 indexes\master-index.json，帮我更新近 30 天公开漏洞与工具 release，并把不确定内容放入 needs_review。
```

或：

```text
请调用 SecKB Skills，针对本地项目路径 <path> 的某个漏洞候选读取 SecKB 模板，做授权范围内的最小化动态验证，并生成 evidence manifest。证据不足时输出为什么不能提交报告。
```

## 重要边界

- 不对互联网真实第三方目标做未授权扫描、利用、批量探测、压测、撞库、绕过、持久化、横向移动或数据破坏。
- 不做 MITM 方向分析。
- 不把工具告警、标题、截图、二次转载、AI 摘要或低可信 PoC 当作 confirmed 证据。
- 不把 SRC 禁止边界写入执行流程。
- 不把 CVE 当成通用模板。
- 不把工具 release 当成漏洞证据。
- 不读取真实敏感数据证明影响。

## 质量门槛

记录进入 `promoted` 必须满足：

1. 至少一个高可信来源。
2. 明确日期。
3. 明确版本或适用范围。
4. 明确影响。
5. 明确边界。
6. 有误报条件。
7. 有不可报告原因。
8. 有修复建议。
9. 有本机或授权环境动态验证方式。
10. 有 tags 和索引入口。

不满足则进入 `needs_review`，存在冲突进入 `conflict`，过期进入 `stale`，低可信或无价值进入 `rejected`。

## v3 新增测试与治理能力

v3 增加以下可执行检查：

```powershell
python .\scripts\claude_code_replay.py .	ests\claude-code-replayeplay-cases.json .eports\claude-code-replay-dryrun.json
python .\scripts\quality_gate_stress.py
python .\scripts\check_index_consistency.py .	estdata\index-consistency --output .eports\index-consistency.json
python .\scripts\dashboard_build.py .	estdata\quality-gateecords_100.json .eports\dashboard.html --format html
python .\scripts	emplate_confusion_test.py
```

这些脚本只做触发回放、质量门禁、索引一致性、dashboard 和模板混淆测试，不执行漏洞利用，不扫描第三方目标。
