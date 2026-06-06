# Evidence Manifest 证据清单生成规范

用途：把请求摘要、响应摘要、截图、代码证据、QG 评分、资产账本统一登记到一个 manifest 中，便于 07 做质量门禁和最终报告。该能力是“基于文档延伸”。

## 输入来源

- `asset-ledger.*.jsonl`：资产账本。
- `requests/`：请求样本或摘要。
- `responses/`：响应摘要，不保存完整敏感值。
- `screenshots/`：浏览器截图。
- `code-evidence/`：代码、配置、构建产物的定位摘要。
- `qg-finding-score.md`：QG-01 到 QG-10 的逐发现评分。

## 生成命令

```bash
python scripts/report-to-manifest.py \
  --project-name local-project \
  --project-root /path/to/project \
  --base-url http://127.0.0.1:3000 \
  --asset-ledger asset-ledger.final.jsonl \
  --request-dir evidence/requests \
  --response-dir evidence/responses \
  --screenshot-dir evidence/screenshots \
  --code-evidence evidence/code \
  --qg-score qg-finding-score.md \
  --out evidence-manifest.json
```

## 质量规则

- Manifest 只登记证据，不自动证明漏洞成立。
- 缺失路径会记录为缺口，不得被引用为已执行证据。
- 标记 `check_required` 的条目必须先脱敏再进入最终报告。
- 每个可报告发现至少应关联：动态请求/响应摘要、代码或配置来源、QG 评分、复现次数。
