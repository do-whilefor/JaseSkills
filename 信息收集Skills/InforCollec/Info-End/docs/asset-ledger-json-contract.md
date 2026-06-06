# 资产账本统一 JSON 交接契约

用途：让 03、04、05、06、07 之间用同一资产账本结构交接，降低 Claude 自由发挥导致的字段漂移。该契约是“基于文档延伸”，用于机器可校验地落实原文档的资产账本字段。

## 文件格式

优先使用 JSONL：每行一个资产对象，均符合 `schemas/asset-ledger.schema.json`。

推荐文件名：

- `asset-ledger.source.jsonl`：03 从源码/配置/构建产物提取。
- `asset-ledger.runtime.jsonl`：04 从动态验证回填。
- `asset-ledger.browser.jsonl`：05 从浏览器存储和角色差分回填。
- `asset-ledger.edge.jsonl`：06 从偏门补漏回填。
- `asset-ledger.final.jsonl`：07 质量门禁后的最终账本。

## 最小对象

```json
{
  "schema_version": "1.0",
  "asset_id": "AS-001",
  "asset_type": "api_endpoint",
  "source": {"kind": "source_code", "file": "src/routes.ts", "line": 12, "tool": "route-artifact-extract.py", "source_asset_id": null},
  "static_location": "src/routes.ts:12",
  "runtime": {"url": "http://127.0.0.1:3000/api/users", "host": "127.0.0.1", "port": 3000, "path": "/api/users", "method": "GET", "protocol": "http"},
  "auth_required": null,
  "auth_state": "not_tested",
  "role": null,
  "exposed_info_types": ["unknown"],
  "verification_status": "static_candidate",
  "evidence_ids": [],
  "risk": "unknown",
  "why_suspicious": "源码中存在可访问 API 路由。",
  "why_reportable_or_not": "尚未动态验证，不能报告。",
  "non_reportable_reason": "只能静态命中，运行态未验证。",
  "qg_status": {},
  "created_at": null,
  "updated_at": null,
  "notes": null
}
```

## Skill 交接规则

- 03 只能创建 `static_candidate`。
- 04 可以把状态推进到 `runtime_accessible`、`pending_confirmation`、`non_reportable`。
- 05 只能补充角色、浏览器存储、认证状态，不得单独把候选升级为可报告。
- 06 只能生成新增候选和补漏清单，必须回流 04。
- 07 才能在 QG 全部满足后标记 `verified_reportable`。

## 验收

- 每条资产必须有 `asset_id`。
- 每条资产必须有 `why_suspicious` 和 `why_reportable_or_not`。
- 没有动态证据的资产不得是 `verified_reportable`。
- 敏感内容不得出现在 JSON 值中，只允许脱敏样本、长度、类型、hash。
