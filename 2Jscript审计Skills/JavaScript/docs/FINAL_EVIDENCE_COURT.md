# 终极反向审判 / 证据法庭说明

本文件记录第三层反向审计机制。它的目标不是提高评价，而是把所有证据不足的能力降级，并输出可执行的 P0 修复和验收链。

## 运行命令

```bash
python scripts/final_evidence_court_audit.py . --json tests/last-final-evidence-court.json --md tests/last-final-evidence-court.md
python scripts/verify_final_court_assets.py .
python scripts/package_self_check.py .
```

## 严格降级规则

- 未发现 parser backend：AST / semantic audit 降级为 missing / fake-ready。
- 未发现 Source Map parser：Source Map 能力降级为 partial/doc-only。
- 未发现 Playwright/Burp/HAR bridge：动态验证降级为未动态验证。
- 未发现 role/tenant replay：严重漏洞发现降级为缺少多角色多租户验证。
- 未发现 schema validator：证据链降级为证据不可强校验。
- 未发现 report generator：报告闭环降级为无法闭环到报告。
- 未发现 dashboard generator：dashboard 降级为展示层伪闭环。

## 不改变原有能力的要求

本补丁只新增 `14-js-skills-evidence-court`、数据矩阵、schema、模板、fixture 和自检脚本，不删除原有 `knowledge/` 与 `templates/`。后续真实修复必须通过 hash baseline 证明未破坏知识库和漏洞模板。
