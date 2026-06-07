# SOURCE_TO_SKILL_RULE 映射

- 本机授权边界 → 所有 SKILL.md、tools/quality_gate.py、scripts/info_collect_orchestrator.py。
- 不伪造漏洞/证据 → knowledge/anti_hallucination_evidence_law.md、tools/quality_gate.py、tools/evidence_builder.py。
- 完整信息收集 → knowledge/information_collection_attack_surface_matrix.md、tools/route_extractor.py、scripts/auth_graph_builder.py。
- JS 顶级审计 → knowledge/js-patterns/top_tier_js_audit_matrix.md、tools/js_asset_extractor.py、scripts/js_audit_graph_builder.py。
- 严重漏洞 38 类 → scripts/detectors/registry.json、knowledge/vulnerability-patterns/severe_vuln_38_matrix.md、vulnerability_templates/。
- 动态验证闭环 → scripts/candidate_to_replay_plan.py、scripts/info_collect_orchestrator.py、tools/quality_gate.py。
- promoted/needs_review/blocked → tools/quality_gate.py、schemas/quality_result.schema.json、manifests/CAPABILITY_PROMOTION_STATUS.json。
