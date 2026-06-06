#!/usr/bin/env python3
from __future__ import annotations
import json, re, sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
errors: list[str] = []

for d in sorted(root.glob('[0-9][0-9]-*')):
    if d.is_dir() and not (d / 'SKILL.md').exists():
        errors.append(f'missing SKILL.md: {d.relative_to(root)}')

for p in root.rglob('*'):
    rel = p.relative_to(root).as_posix()
    if p.name == '__pycache__' or p.suffix == '.pyc' or p.name in {'.DS_Store', 'Thumbs.db'} or p.suffix in {'.tmp', '.bak', '.swp'}:
        errors.append(f'forbidden cache file: {rel}')
    if p.is_file() and re.search(r'(^|/)(CHANGELOG|RELEASE_NOTES|RELEASE_MANIFEST|VERSION)$', rel):
        errors.append(f'forbidden release/version file: {rel}')
    if p.is_file() and re.search(r'(20260606|REBUILD|REPAIR|VALIDATION_EVIDENCE|WINDOWS_CODE_AUDIT|RUNTIME_COMPATIBILITY)', rel, re.I):
        errors.append(f'forbidden dated/update artifact: {rel}')

required = [
    'README.md', 'SKILL.md', 'package.json', 'requirements.txt',
    'docs/CAPABILITY_INDEX.md', 'docs/DOCUMENT_MAPPING_MATRIX.md', 'docs/ROUTING_TABLE.md',
    'docs/QUALITY_GATE_SPEC.md', 'docs/RUNBOOK.md', 'docs/MAINTENANCE.md',
    'templates/evidence-manifest.json', 'schemas/evidence-manifest.schema.json',
    'tests/trigger-test-cases.json', 'tests/sample-manifests/insufficient.json',
    '12-js-skills-extreme-reviewer/SKILL.md', '13-js-skills-second-pass-reverse-auditor/SKILL.md',
    '14-js-skills-evidence-court/SKILL.md', '15-js-top-tier-collection-analysis-audit/SKILL.md',
    '16-js-hidden-api-parameter-modeling/SKILL.md', '17-js-browser-lazyload-replay/SKILL.md',
    '18-js-backend-accepted-param-diff/SKILL.md', '19-js-severe-vulnerability-verification/SKILL.md',
    '20-js-self-audit-verdict/SKILL.md', '21-js-runtime-evidence-orchestration/SKILL.md',
    '22-js-framework-schema-deep-parser/SKILL.md', '23-js-oss-replay-and-environment-gate/SKILL.md',
    'installers/install.sh', 'installers/install.ps1',
    'tools/windows/install.ps1', 'tools/windows/validate.ps1', 'tools/windows/import-authorized-target.ps1',
    'tools/windows/run.cmd', 'tools/windows/validate.cmd',
    'scripts/install_and_env_check.py', 'scripts/js_cross_platform_runner.mjs',
    'scripts/js_windows_env_check.py', 'scripts/js_windows_validation_suite.py',
    'scripts/js_top_tier_collect.py', 'scripts/js_top_tier_analyze.py', 'scripts/js_top_tier_quality_gate.py',
    'scripts/js_runtime_evidence_bridge.py', 'scripts/js_role_tenant_diff.py',
    'scripts/js_playwright_safe_replay_executor.py', 'scripts/js_backend_acceptance_probe.py',
    'scripts/js_top_tier_report_generator.py', 'scripts/js_api_parameter_model.py',
    'scripts/js_backend_param_diff.py', 'scripts/js_browser_lazyload_replay_plan.py',
    'scripts/js_severe_js_candidate_mapper.py', 'scripts/js_self_audit_matrix.py',
    'scripts/run_js_top_tier_fixture_tests.py', 'scripts/verify_js_top_tier_assets.py',
    'scripts/js_runtime_artifact_importer.py', 'scripts/js_runtime_evidence_manifest.py',
    'scripts/js_graphql_ws_runtime_replay.py', 'scripts/js_wrapper_resolver.py',
    'scripts/js_sourcemap_reconstructor.py', 'scripts/js_cdn_history_asset_enumerator.py',
    'scripts/js_service_worker_cache_auditor.py', 'scripts/js_framework_build_parser.py',
    'scripts/js_schema_alignment.py', 'scripts/js_hidden_feature_extractor.py',
    'scripts/js_business_flow_template_generator.py', 'scripts/js_evidence_dashboard_drilldown.py',
    'scripts/js_oss_replay_registry.py', 'scripts/js_real_oss_replay_executor.py',
    'scripts/js_authorized_target_import_gate.py', 'scripts/js_role_tenant_authorization_replay.py',
    'scripts/js_hidden_param_acceptance_matrix.py', 'scripts/js_runtime_detector_binder.py',
    'scripts/js_semantic_graph_builder.py', 'scripts/js_detector_registry_runner.py',
    'scripts/js_scope_guard.py', 'scripts/js_schema_validator.py', 'scripts/js_adversarial_harness.py',
    'scripts/js_unit_tests.py', 'scripts/js_full_validation_suite.py', 'scripts/js_p1_validation_suite.py',
    'scripts/backends/js/babel_extract.mjs', 'scripts/backends/js/typescript_extract.mjs',
    'schemas/js-top-tier-ledger.schema.json', 'schemas/js-top-tier-finding.schema.json',
    'schemas/js-api-parameter-model.schema.json', 'schemas/js-backend-param-diff.schema.json',
    'schemas/js-browser-replay-plan.schema.json', 'schemas/js-runtime-evidence.schema.json',
    'schemas/js-backend-acceptance-evidence.schema.json', 'schemas/js-severe-candidate-map.schema.json',
    'schemas/js-self-audit-matrix.schema.json', 'schemas/js-evidence-manifest.schema.json',
    'schemas/js-wrapper-resolution.schema.json', 'schemas/js-sourcemap-reconstruction.schema.json',
    'schemas/js-cdn-history-assets.schema.json', 'schemas/js-service-worker-cache-audit.schema.json',
    'schemas/js-framework-build-artifacts.schema.json', 'schemas/js-schema-alignment.schema.json',
    'schemas/js-hidden-feature-signals.schema.json', 'schemas/js-business-flow-templates.schema.json',
    'schemas/js-graphql-ws-runtime-replay.schema.json', 'schemas/js-oss-replay-registry.schema.json',
    'schemas/js-env-check.schema.json', 'schemas/js-windows-env-check.schema.json',
    'schemas/js-windows-validation-run.schema.json', 'schemas/js-runtime-artifact-bundle.schema.json',
    'schemas/js-authorized-target-import.schema.json', 'schemas/js-role-tenant-authorization-result.schema.json',
    'schemas/js-hidden-param-acceptance-matrix.schema.json', 'schemas/js-runtime-detector-binding.schema.json',
    'schemas/js-real-oss-replay-result.schema.json', 'schemas/js-semantic-graph.schema.json',
    'schemas/js-detector-finding.schema.json', 'schemas/js-detector-registry.schema.json',
    'schemas/js-adversarial-result.schema.json', 'schemas/js-scope.schema.json',
    'templates/js-top-tier-report.md', 'templates/js-api-parameter-model.md',
    'templates/js-hidden-param-validation.md', 'templates/js-browser-replay-plan.md',
    'templates/js-runtime-evidence.md', 'templates/js-backend-acceptance-evidence.md',
    'templates/js-self-audit-verdict.md', 'templates/js-evidence-manifest.md',
    'templates/js-oss-replay-sample.md', 'templates/js-business-flow-validation.md',
    'templates/js-detector-registry-finding.md',
    'knowledge/js-top-tier-audit-playbook.md', 'knowledge/js-hidden-api-parameter-playbook.md',
    'knowledge/js-runtime-evidence-orchestration.md', 'knowledge/js-framework-schema-parsing.md',
    'data/js_top_tier_collectors.json', 'data/js_top_tier_detectors.json',
    'data/js_top_tier_quality_caps.json', 'data/js_top_tier_runtime_requirements.json',
    'data/js_hidden_api_param_rules.json', 'data/js_browser_replay_actions.json',
    'data/js_detector_registry_v2.json',
    'fixtures/js-top-tier-samples/app/index.html',
    'fixtures/js-top-tier-samples/app/static/js/app.js',
    'fixtures/js-top-tier-samples/app/static/js/app.js.map',
    'fixtures/js-hidden-param-samples/frontend/app.js',
    'fixtures/js-hidden-param-samples/backend/users_controller.ts',
    'fixtures/js-hidden-param-samples/sample.har',
    'fixtures/runtime-replay/graphql-ws-scenarios.json',
    'fixtures/runtime-artifacts-import-sample/artifact-origin.json',
    'fixtures/adversarial-js-hallucination/cases.json',
    'fixtures/worldclass-semantic-sample/app.js',
]

for r in required:
    if not (root / r).exists():
        errors.append(f'missing required file: {r}')

knowledge_files = [p for p in (root / 'knowledge').glob('*') if p.is_file()] if (root / 'knowledge').exists() else []
template_files = [p for p in (root / 'templates').glob('*') if p.is_file()] if (root / 'templates').exists() else []
if len(knowledge_files) < 8:
    errors.append('knowledge preservation check failed: expected at least 8 knowledge files')
if len(template_files) < 18:
    errors.append('template preservation check failed: expected at least 18 template files')

pkg_path = root / 'package.json'
if pkg_path.exists():
    try:
        pkg = json.loads(pkg_path.read_text(encoding='utf-8'))
        if 'version' in pkg:
            errors.append('package.json must not carry release/version metadata in the cleaned package')
        scripts = pkg.get('scripts', {})
        if scripts.get('windows:validate') != 'node scripts/js_cross_platform_runner.mjs windows:validate':
            errors.append('package.json windows:validate must use the cross-platform runner')
    except Exception as e:
        errors.append(f'package.json parse failed: {e}')

print(json.dumps({'ok': not errors, 'errors': errors}, ensure_ascii=False, indent=2))
raise SystemExit(1 if errors else 0)
