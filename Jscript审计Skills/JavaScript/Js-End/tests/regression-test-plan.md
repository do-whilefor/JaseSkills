# Regression Test Plan

覆盖：正常任务、模糊任务、负样本、误触发、漏触发、文档冲突、文档缺失、路径幻觉、工具幻觉、Prompt Injection、输出格式、质量门禁、多 Skill 协作、最小路径、专家路径。

运行：`python3 scripts/skill_trigger_tester.py` 和 `python3 scripts/package_self_check.py .`。


## 极限评审回归

1. `python scripts/verify_extreme_review_assets.py .` 必须通过。
2. `python scripts/extreme_skills_review.py . --json-out tests/last-extreme-review.json --markdown tests/last-extreme-review.md` 必须生成 JSON 与 Markdown。
3. 当 Markdown 声明 Babel/TypeScript/tree-sitter/Playwright/Burp/HAR 但没有对应脚本时，报告必须降级为 `doc-only` 或 `partial`，不能输出 `ready`。
4. 当包中出现 `__pycache__`、`.pyc`、`.tmp`、`.bak`、`.swp`、`.DS_Store`、`Thumbs.db` 时，`package_self_check.py` 必须失败。


## 第二轮反向审查回归

```bash
python scripts/verify_second_pass_assets.py .
python scripts/second_pass_reverse_audit.py . --json-out tests/last-second-pass-review.json --markdown tests/last-second-pass-review.md
```

验收：

- JSON 中 `corrected_scores.总分` 存在。
- 没有真实 parser backend 时，`runtime_evidence.parser_backend` 必须为空。
- 没有 Playwright/Burp/HAR bridge 时，`runtime_evidence.runtime_bridge` 必须为空。
- 没有 detector harness 时，`runtime_evidence.detectors` 必须为空。
- Markdown 必须包含 9 个主章节。


## Final Evidence Court Regression

```bash
python scripts/final_evidence_court_audit.py . --json tests/last-final-evidence-court.json --md tests/last-final-evidence-court.md
python scripts/verify_final_court_assets.py .
python scripts/package_self_check.py .
```

验收：输出必须包含 20 起 JS 收集漏报事故、10 类伪能力拆穿、30 类严重漏洞漏报、工程验尸、失败惩罚评分和不可辩解 P0。没有真实 runtime backend 的能力必须降级。


## JS Top Tier fixture 回归

```bash
python scripts/verify_js_top_tier_assets.py .
python scripts/run_js_top_tier_fixture_tests.py .
```

验收：必须收集 JS、Source Map、GraphQL/WebSocket 候选，并在缺动态证据时保持 `not-top-tier`。
