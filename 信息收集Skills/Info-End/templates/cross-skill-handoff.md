# 跨 Skill 交接模板

## 交接来源
- 来源 Skill：
- 交接时间：
- 当前任务类型：

## 输入来源
-

## 候选
| 编号 | 类型 | 来源 | 下一步需要哪个 Skill |
|---|---|---|---|

## 已验证项
| 编号 | 证据编号 | 结论 | 质量门禁状态 |
|---|---|---|---|

## 待确认项
| 编号 | 缺失证据 | 下一步最小验证 |
|---|---|---|

## 不可报告项
| 编号 | 不可报告原因 |
|---|---|

## 不可交付原因
-

## JSON Schema 交接要求

跨 Skill 交接资产时，优先使用 JSONL，每行符合 `schemas/asset-ledger.schema.json`。如果只能输出 Markdown 表格，必须包含能映射到 schema 的字段：asset_id、asset_type、source、runtime、auth_state、role、verification_status、evidence_ids、risk、why_suspicious、why_reportable_or_not。
