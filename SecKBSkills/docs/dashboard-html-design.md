# Dashboard 静态 HTML 设计

## 显示内容

1. 来源可信度：平均值、低可信记录、unknown source。
2. Freshness：0-30 天、31-90 天、90 天以上、unknown。
3. 冲突：`review_status=conflict` 或存在 `source_conflict_fields` 的记录。
4. 人工确认队列：`needs_review`、`conflict`、`stale` 优先。

## 设计约束

- 静态 HTML，不依赖外部网络、CDN、数据库。
- 只展示知识库治理状态，不确认漏洞存在。
- 不展示真实敏感数据。
- 可由 `scripts/dashboard_build.py --format html` 生成。
