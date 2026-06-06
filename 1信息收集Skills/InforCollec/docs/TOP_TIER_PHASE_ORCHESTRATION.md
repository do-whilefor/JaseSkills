# 信息收集总控 Phase 设计

| Phase | 名称 | 触发条件 | 输入 | 输出 | 调用脚本 | 证据字段 | 失败处理 | 质量门槛 | 测试样例 |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 授权范围确认 | 任意执行型信息收集任务 | `--input`, `--scope` | scope 结果 | `scripts/scope_guard.py` | `scope_id`, `source_file` | 越界返回失败并停止 | out-of-scope 必须阻断 | `test_top_tier_scope_blocks_out_of_scope` |
| 1 | 项目结构识别 | 授权范围通过 | 项目根目录 | 模块与目录 | `scripts/project_fingerprint.py` | `project_structure` | 无文件则 unverifiable | 至少输出项目结构 | `normal_project` |
| 2 | 语言/框架/依赖识别 | 发现源码/manifest | 项目根目录 | 技术栈 | `project_fingerprint.py`, `dependency_surface_collector.py` | `language_detected`, `framework_detected` | parser 不可用标 planned | 至少识别语言或 manifest | `express_next`, `django_fastapi`, `spring_laravel`, `go_rust` |
| 3 | 路由/API/入口点识别 | 发现源码/API 规格 | 项目根目录 | 路由/API 候选 | `route_api_extractor.py` | `backend_or_frontend_route`, `openapi_path_operation` | 无动态证据保持 candidate | 输出 route/api 候选或说明缺失 | `api_graphql_ws` |
| 4 | 认证/鉴权/角色/租户识别 | 发现 auth/role/tenant 字段 | 项目根目录 | 边界候选 | `auth_boundary_collector.py` | `auth_relevance`, `tenant_relevance`, `role_relevance` | 不能确认业务语义时 needs_review | 高价值边界进入人工复核 | `seed_mock_fixture` |
| 5 | 配置/部署/CI/CD/云资产识别 | 发现 config/IaC/CI | 项目根目录 | 配置线索 | `config_secret_signal_collector.py` | `data_sensitivity`, `raw_value_hash` | secret 必须脱敏 | 不泄露完整 secret | `docker_k8s_ci` |
| 6 | 前端 JS/sourcemap/chunk/SW/manifest | 发现 JS/前端产物 | 项目根目录 | 前端隐藏信息 | `js_deep_info_collector.py` | `endpoint_relevance` | source map 只作为候选 | JS artifacts 必须入证据 | `sourcemap_frontend`, `service_worker` |
| 7 | 隐藏信息发现 | 二轮补漏 | 项目根目录 | 隐藏候选 | `hidden_info_collector.py` | `needs_human_review` | 旧接口不得确认可访问 | 隐藏候选进入 review | `hidden_api`, `seed_mock_fixture` |
| 8 | 敏感数据与危险操作入口识别 | 发现 secret/危险脚本/依赖 | 项目根目录 | 高价值候选 | `dependency_surface_collector.py`, `config_secret_signal_collector.py` | `severity_hint` | 原文不输出 | 触发 redaction gate | `false_positive_negative` |
| 9 | 攻击面知识图谱生成 | manifest 已生成 | evidence manifest | graph JSON | `attack_surface_graph_builder.py` | Evidence 链接 | 无 manifest 则失败 | 节点边必须来自 evidence | `fixture replay` |
| 10 | 证据归档与报告输出 | collector 输出完成 | collector JSON/JSONL | manifest/report | `evidence_manifest_builder.py` | schema required fields | schema 不通过则失败 | schema validator PASS | `test_top_tier_manifest_and_quality_gate` |
| 11 | 质量门槛检查 | manifest 已生成 | manifest | QG 结果 | `info_quality_gate.py` | `linked_report_section` | 分数不足保持 partial | 默认 70 分 | `test_top_tier_manifest_and_quality_gate` |
| 12 | 人工复核队列输出 | 有 needs_review 或高价值候选 | manifest | review queue | `human_review_queue.py` | `review_id` | 不输出完整 secret | review queue 非空 | `test_top_tier_review_queue` |
