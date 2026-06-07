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
python -m pytest -q tests
bash scripts/run-package-selftest.sh . /tmp/info-skills-selftest

# 本机运行态盘点
./scripts/local-runtime-inventory.sh /path/to/project runtime-inventory.md

# 静态路由与构建产物候选
python scripts/route-artifact-extract.py /path/to/project -o static-candidates.jsonl
python scripts/code-surface-inventory.py /path/to/project -o code-surface-inventory.jsonl
python scripts/codegraph-builder.py /path/to/project -o codegraph.jsonl

# JS 资产、manifest、endpoint 候选
python scripts/js-asset-audit.py /path/to/project -o js-asset-candidates.jsonl
python scripts/js-manifest-expander.py /path/to/project -o js-manifest-assets.jsonl
node scripts/js-ast-endpoint-extractor.mjs /path/to/project -o js-ast-endpoints.jsonl

# 配置、依赖和信息面归一化
python scripts/config-dependency-inventory.py /path/to/project -o config-dependency-inventory.jsonl
python scripts/info-surface-normalizer.py   --input js-asset-candidates.jsonl   --input js-manifest-assets.jsonl   --input code-surface-inventory.jsonl   --input config-dependency-inventory.jsonl   --out info-surface.normalized.jsonl

# source/sink 候选和严重漏洞入口候选
python scripts/source-sink-dataflow.py /path/to/project -o source-sink-candidates.jsonl
python detectors/c01_c05_access_control.py --input info-surface.normalized.jsonl --out access-control-candidates.jsonl
python detectors/c06_c30_high_impact_candidates.py --input info-surface.normalized.jsonl --out high-impact-candidates.jsonl

# 非破坏性动态探测，默认只允许 localhost/127.0.0.1
./scripts/exposure-probe-safe.sh --base http://127.0.0.1:3000 --paths paths.txt --out probe-results.tsv --repeat 2

# 授权内网目标必须使用精确 host 白名单
./scripts/exposure-probe-safe.sh --base http://app.internal:8080 --paths paths.txt --allow-host app.internal --out probe-results.tsv

# Playwright / WebSocket 运行态契约；无可用 runtime 时只输出 contract-only，不伪装动态证据
node scripts/playwright-har-role-matrix.mjs --config tests/fixtures/role_matrix/config.json --out runtime-evidence
node scripts/ws-readonly-capture.mjs --url ws://127.0.0.1:3000/ws --out ws-evidence.json --contract-only

# 报告、证据 manifest 和质量门
python scripts/report-to-manifest.py --project-name local-project --project-root /path/to/project --out evidence-manifest.json
python scripts/qg-jsonl-score.py --input findings.jsonl --manifest evidence-manifest.json --out qg-results.jsonl --fail-on-error
python scripts/quality-gate-check.py draft-report.md
```


## 工程化目录与一键命令

包内保留 `knowledge/`、`templates/`、`detectors/`、`rules/` 和漏洞/发现模板，并提供可执行工程层：

- `collectors/`：route、JS asset、config、dependency、docs、CI/CD、IaC、GraphQL、WebSocket、sourcemap、hidden parameter collectors。
- `analyzers/`：project fingerprint、endpoint/parameter、auth、role/tenant、frontend/backend correlation、secret redaction、evidence quality analyzers。
- `quality/`：scope、secret redaction、evidence completeness、anti-hallucination、coverage 和 unified gates。
- `reports/`：Markdown、JSON、CSV、evidence manifest summary 报告生成器。
- `info_end_run.py`：一键执行 collectors -> evidence manifest -> analyzers -> quality gates -> reports。

```bash
python info_end_run.py   --input /path/to/authorized/project   --scope /path/to/authorized/project   --output /tmp/info-end-out   --no-network   --max-files 5000   --scan-profile standard
```

`--no-network` 是保留边界语义；新工程 pipeline 默认不联网。所有静态发现默认 `candidate`，敏感、隐藏、权限/租户相关或无法完成复核的发现保持 `needs_review`，不得伪装为 confirmed。

详见 `docs/ENGINEERING_SYSTEM_AUDIT.md`。

## 硬性边界

- 只审计本机、授权仓库、授权靶场、授权开源项目和明确授权服务。
- 不访问、攻击或验证真实第三方目标。
- 不输出完整敏感值；必须脱敏、截断或哈希。
- 不执行破坏性 payload，不做持久化、隐蔽控制、数据窃取或横向移动。
- 静态候选、工具输出、模板示例、矩阵命中均不等于确认漏洞。
- 缺少运行态证据、角色/租户验证、质量门和人工复核时，发现必须保持 `candidate` 或 `needs_review`。

## 信息收集增强命令

```bash
# 隐藏信息候选：注释、source map、minified JS、GraphQL operation、service worker、manifest、feature flag、CI/CD、Docker/K8s/Terraform、测试 seed、反向代理、robots/sitemap/well-known 等
python scripts/hidden-info-miner.py /path/to/project -o hidden-info-candidates.jsonl

# API 规格：OpenAPI/Swagger JSON/YAML、Postman collection、GraphQL schema/operation、protobuf/gRPC
python scripts/api-spec-inventory.py /path/to/project -o api-spec-candidates.jsonl

# 40 项信息收集覆盖面自审；可把多个 JSONL 输出喂入做证据信号检查
python scripts/surface-coverage-audit.py --root . \
  --jsonl hidden-info-candidates.jsonl \
  --jsonl api-spec-candidates.jsonl \
  --out info-coverage-audit.json
```

这些增强脚本默认只读、离线、候选级输出；不访问网络，不证明漏洞，不输出完整敏感值。候选需要回流 `04-dynamic-exposure-validation`、`07-evidence-reporting-quality-gate` 和人工复核。

## 总控信息收集命令

```bash
python scripts/info_collect_orchestrator.py \
  --input /path/to/authorized/project \
  --scope /path/to/authorized/project \
  --output /tmp/info-end-out \
  --no-network \
  --redact-secrets \
  --scan-profile standard
```

说明：该命令只面向本机授权项目，默认离线、只读、非破坏。输出是候选信息、证据 manifest、质量门结果、人工复核队列、图谱和报告草稿；没有授权动态验证和人工复核前，不得写成确认漏洞。


## 工程边界

JS 严格 AST 模式必须使用真实 AST parser（优先 @babel/parser，回退 TypeScript compiler API；无 parser 则失败而非伪装 AST）。collector/schema 主流程校验、runtime-evidence schema、runtime 结果合并、coverage skipped reason 强制断言、analyzer 合约测试、monorepo 与 false-positive fixtures 均为可执行校验项。JS callgraph、框架路由、参数绑定和 role/tenant matrix 仍为候选级静态能力，不宣称完整验证。可直接复制目录到 `.claude/skills`。

## Windows 快速运行

Windows 上推荐使用 `py -3 info_end_run.py --input . --scope . --output out\info-end`。自检与清理脚本提供 `.cmd`/`.ps1` 包装器；详见 `docs/WINDOWS_RUNBOOK.md`。
