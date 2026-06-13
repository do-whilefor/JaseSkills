# Scripts

这些脚本用于 SecKB 知识库治理，不包含攻击性验证逻辑。

- `init_seckb.ps1`：初始化本地 SecKB 目录。
- `update_sources.ps1`：占位采集入口；无网络或未配置源时只生成任务清单。
- `normalize_records.py`：把 JSON/JSONL 记录补齐字段。
- `dedupe_records.py`：按 ID、URL、标题去重。
- `score_sources.py`：按来源类型计算可信度。
- `build_indexes.py`：生成 indexes。
- `check_freshness.py`：检查 last_checked、published_date、updated_date。
- `quality_gate.py`：检查 promoted 是否满足质量门槛。
- `rag_route_tests.py`：执行负样本路由测试骨架。
- `dashboard_build.py`：生成静态 dashboard Markdown。
