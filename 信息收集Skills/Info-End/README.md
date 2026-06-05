# Info Exposure Audit Skills

这套 Skills 用于本机、授权项目的信息暴露面审计、JS 资产发现、配置与依赖采集、非破坏性动态验证、证据整理和质量门禁。所有输出默认是候选或证据摘要；没有授权范围、动态证据、脱敏、质量门和人工复核时，不得把候选写成确认漏洞。

## 安装

将整个 `info-exposure-audit-skills` 目录放入 Claude Skills 目录：

```bash
mkdir -p ~/.claude/skills
cp -r info-exposure-audit-skills ~/.claude/skills/
```

Windows 常见目录为 `%USERPROFILE%\.claude\skills\`，以你的实际 Claude 配置为准。

## 推荐调用方式

```text
调用 info-exposure-audit-skills，对当前本机已运行的授权项目做信息暴露面审计。先确认项目根目录、运行方式、端口、Base URL、账号角色和禁止范围，再建立信息面资产账本，最后做非破坏性验证和证据质量门检查。
```

## 目录说明

- `CAPABILITY_INDEX.md`：能力索引和触发路由。
- `00-master-info-exposure-orchestrator/`：总控入口。
- `01-scope-runtime-intake/`：授权范围、运行态输入、账号角色和禁止范围确认。
- `02-runtime-entry-enumeration/`：本机运行态入口枚举。
- `03-static-route-artifact-mining/`：源码、路由、JS、配置、依赖和构建产物候选提取。
- `04-dynamic-exposure-validation/`：非破坏性动态验证。
- `05-role-diff-browser-storage/`：角色差异、浏览器存储和运行态契约。
- `06-artifact-cache-container-edge-cases/`：偏门入口、缓存、容器、包产物和二轮补漏。
- `07-evidence-reporting-quality-gate/`：证据 manifest、脱敏、质量门和报告模板。
- `08-skill-adversarial-audit-regression/`：Skills 自审、触发路由压测、反幻觉和回归测试。
- `scripts/`：只读、非破坏、本机授权范围内的辅助脚本。
- `detectors/`：严重漏洞入口候选规则和覆盖矩阵。
- `schemas/`：资产、信息面、运行态证据和 finding 证据链 schema。
- `templates/`：报告、资产账本、质量门、验证手册和漏洞/发现模板。
- `knowledge/`：知识库保留目录。清理发布包时不得删除。
- `tests/`：自测和回归 fixture。

## 常用命令

```bash
# 结构自检与回归测试
python3 -m pytest -q tests
bash scripts/run-package-selftest.sh . /tmp/info-skills-selftest

# 本机运行态盘点
./scripts/local-runtime-inventory.sh /path/to/project runtime-inventory.md

# 静态路由与构建产物候选
python3 scripts/route-artifact-extract.py /path/to/project -o static-candidates.jsonl
python3 scripts/code-surface-inventory.py /path/to/project -o code-surface-inventory.jsonl
python3 scripts/codegraph-builder.py /path/to/project -o codegraph.jsonl

# JS 资产、manifest、endpoint 候选
python3 scripts/js-asset-audit.py /path/to/project -o js-asset-candidates.jsonl
python3 scripts/js-manifest-expander.py /path/to/project -o js-manifest-assets.jsonl
node scripts/js-ast-endpoint-extractor.mjs /path/to/project -o js-ast-endpoints.jsonl

# 配置、依赖和信息面归一化
python3 scripts/config-dependency-inventory.py /path/to/project -o config-dependency-inventory.jsonl
python3 scripts/info-surface-normalizer.py   --input js-asset-candidates.jsonl   --input js-manifest-assets.jsonl   --input code-surface-inventory.jsonl   --input config-dependency-inventory.jsonl   --out info-surface.normalized.jsonl

# source/sink 候选和严重漏洞入口候选
python3 scripts/source-sink-dataflow.py /path/to/project -o source-sink-candidates.jsonl
python3 detectors/c01_c05_access_control.py --input info-surface.normalized.jsonl --out access-control-candidates.jsonl
python3 detectors/c06_c30_high_impact_candidates.py --input info-surface.normalized.jsonl --out high-impact-candidates.jsonl

# 非破坏性动态探测，默认只允许 localhost/127.0.0.1
./scripts/exposure-probe-safe.sh --base http://127.0.0.1:3000 --paths paths.txt --out probe-results.tsv --repeat 2

# 授权内网目标必须使用精确 host 白名单
./scripts/exposure-probe-safe.sh --base http://app.internal:8080 --paths paths.txt --allow-host app.internal --out probe-results.tsv

# Playwright / WebSocket 运行态契约；无可用 runtime 时只输出 contract-only，不伪装动态证据
node scripts/playwright-har-role-matrix.mjs --config tests/fixtures/role_matrix/config.json --out runtime-evidence
node scripts/ws-readonly-capture.mjs --url ws://127.0.0.1:3000/ws --out ws-evidence.json --contract-only

# 报告、证据 manifest 和质量门
python3 scripts/report-to-manifest.py --project-name local-project --project-root /path/to/project --out evidence-manifest.json
python3 scripts/qg-jsonl-score.py --input findings.jsonl --manifest evidence-manifest.json --out qg-results.jsonl --fail-on-error
python3 scripts/quality-gate-check.py draft-report.md
```

## 硬性边界

- 只审计本机、授权仓库、授权靶场、授权开源项目和明确授权服务。
- 不访问、攻击或验证真实第三方目标。
- 不输出完整敏感值；必须脱敏、截断或哈希。
- 不执行破坏性 payload，不做持久化、隐蔽控制、数据窃取或横向移动。
- 静态候选、工具输出、模板示例、矩阵命中均不等于确认漏洞。
- 缺少运行态证据、角色/租户验证、质量门和人工复核时，发现必须保持 `candidate` 或 `needs_review`。
