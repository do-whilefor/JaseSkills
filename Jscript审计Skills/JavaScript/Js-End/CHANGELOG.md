# CHANGELOG

## 2026.06.06-clean1 - 2026-06-06

### 保留

- 保留全部 `knowledge/` 知识库文件。
- 保留全部 `templates/` 漏洞模板与报告模板。
- 保留全部子 Skill、schemas、data、fixtures、scripts、tests 中的可复用资产。

### 清理

- 移除运行态 `reports/` 目录。
- 移除 `tests/js-top-tier-last-run/` 运行产物。
- 移除 `*.pyc`、`__pycache__`、`.pytest_cache`、`.DS_Store`、`Thumbs.db`、临时日志和缓存。
- 不移除 fixture、知识库、模板、schema 或脚本。

### 说明更新

- 更新 `README.md`、`SKILL.md`、`VERSION`、`package.json`。
- 新增 `RELEASE_NOTES.md` 与 `RELEASE_MANIFEST.json`。
- 明确证据优先规则：缺 HAR/trace/screenshots/request-response/evidence manifest/role-tenant/backend acceptance 时，严重漏洞不得超过 candidate。

### 验收

- `python scripts/package_self_check.py .`
- `python scripts/verify_js_top_tier_assets.py .`
- `python scripts/run_js_top_tier_fixture_tests.py .`

