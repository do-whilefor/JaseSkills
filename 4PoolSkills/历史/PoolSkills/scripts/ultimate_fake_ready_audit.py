#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_ROOTS = ['common','collectors','analyzers','detectors','dynamic','evidence','quality','report','tools','fuzz','scripts']
PLACEHOLDER_RX = re.compile(r'\b(TODO|FIXME|mock|stub|fake|placeholder|NotImplemented)\b|pass\s*(#.*)?$', re.I | re.M)

CAPABILITIES = [
  ('scope 边界控制', ['common/scope_guard.py'], ['tests/test_scope_enforced.py','tests/adversarial/test_ultimate_anti_fraud.py'], 'usable'),
  ('symlink 越界阻断', ['common/scope_guard.py','evidence/ref_validator.py'], ['tests/test_scope_enforced.py','tests/adversarial/test_ultimate_anti_fraud.py'], 'usable'),
  ('secret 检测与脱敏', ['common/scope_guard.py','evidence/redactor.py','evidence/ref_validator.py'], ['tests/test_evidence_redaction.py','tests/adversarial/test_ultimate_anti_fraud.py'], 'usable'),
  ('evidence manifest 构建', ['evidence/evidence_manifest_builder.py'], ['tests/test_evidence_redaction.py'], 'usable'),
  ('evidence schema 校验', ['quality/quality_gate.py','schemas/evidence-manifest.schema.json'], ['tests/test_evidence_ref_integrity.py'], 'usable'),
  ('tool orchestrator', ['tools/tool_orchestrator.py','tools/tool_registry.yaml'], ['tests/test_tool_orchestrator.py'], 'usable'),
  ('tool wrapper 真实调用', ['tools/tool_orchestrator.py'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'usable'),
  ('工具版本记录', ['tools/tool_orchestrator.py'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'partial'),
  ('Semgrep 调用', ['tools/tool_registry.yaml'], ['scripts/tool_registry_selftest.py'], 'environment-dependent'),
  ('gitleaks/trufflehog 调用', ['tools/tool_registry.yaml'], ['scripts/tool_registry_selftest.py'], 'environment-dependent'),
  ('Playwright 真实浏览器执行', ['dynamic/playwright_runner.py'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'environment-dependent'),
  ('HAR/trace/screenshot/DOM/console/request/response 捕获', ['dynamic/playwright_runner.py'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'partial'),
  ('role/tenant matrix', ['dynamic/role_tenant_matrix.yaml','quality/quality_gate.py'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'partial'),
  ('candidate_to_replay_plan', ['dynamic/candidate_to_replay_plan.py'], ['run_engine_selftest.py'], 'usable'),
  ('replay 执行器', ['dynamic/playwright_runner.py'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'partial'),
  ('positive/negative/blocked/needs_review fixtures', ['tests/fixtures/vulnerable_apps/FIXTURE_INDEX.json'], ['tests/test_detector_fixtures_complete.py'], 'usable'),
  ('quality gate 真阻断', ['quality/quality_gate.py'], ['tests/test_round3_hard_gates.py','tests/adversarial/test_ultimate_anti_fraud.py'], 'usable'),
  ('confirmed/candidate 分级', ['quality/quality_gate.py'], ['tests/test_quality_gate.py'], 'usable'),
  ('report generator', ['report/report_generator.py','schemas/security-report.schema.json'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'usable'),
  ('dashboard 真实数据读取', ['dashboard/current/index.html'], [], 'paper-only'),
  ('JS AST 分析', ['analyzers/lang/js_ts_ast.py','analyzers/lang/probes/TypeScriptAstProbe.js'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'usable'),
  ('sourcemap 还原', ['collectors/js_asset_collector.py'], [], 'paper-only'),
  ('lazy chunk 发现', ['collectors/js_asset_collector.py'], [], 'partial'),
  ('hidden parameter miner', ['collectors/hidden_parameter_collector.py','collectors/js_asset_collector.py'], [], 'partial'),
  ('frontend-backend diff', ['analyzers/frontend_backend_correlation_analyzer.py'], [], 'partial'),
  ('GraphQL operation extractor', ['collectors/js_asset_collector.py'], [], 'partial'),
  ('WebSocket event extractor', ['collectors/js_asset_collector.py'], [], 'partial'),
  ('semantic graph builder', ['analyzers/semantic_graph_builder.py'], ['tests/test_cross_file_dataflow.py'], 'partial'),
  ('source-sink-dataflow', ['analyzers/semantic_graph_builder.py','detectors/detector_runner.py'], ['tests/test_cross_file_dataflow.py'], 'partial'),
  ('auth context', ['collectors/route_collector.py','quality/quality_gate.py'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'partial'),
  ('tenant context', ['quality/quality_gate.py'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'partial'),
  ('detector 独立逻辑', ['detectors/detector_runner.py','detectors/detector_rules.yaml'], ['tests/test_detector_engine.py','scripts/detector_registry_selftest.py'], 'partial'),
  ('0day research harness', ['playbooks/0day_research_playbook.md','fuzz/fuzz_harness.py'], [], 'paper-only'),
  ('fuzz harness', ['fuzz/fuzz_harness.py'], [], 'partial'),
  ('property-based test', ['tests/property/invariants.py'], [], 'paper-only'),
  ('adversarial anti-hallucination harness', ['tests/adversarial/test_ultimate_anti_fraud.py'], ['tests/adversarial/test_ultimate_anti_fraud.py'], 'usable'),
]


def py_defs(path: Path) -> dict:
    if path.suffix != '.py': return {'functions': [], 'classes': [], 'syntax_ok': None}
    try:
        tree = ast.parse(path.read_text(encoding='utf-8', errors='ignore'))
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        return {'functions': funcs, 'classes': classes, 'syntax_ok': True}
    except Exception as e:
        return {'functions': [], 'classes': [], 'syntax_ok': False, 'error': str(e)}


def core_files():
    files=[]
    for root in CORE_ROOTS:
        d=ROOT/root
        if d.exists():
            for p in d.rglob('*'):
                if p.is_file() and p.suffix in {'.py','.yaml','.yml','.json','.js','.go','.java','.rb','.php','.md'}:
                    files.append(p)
    return sorted(files)


def classify(path: Path, text: str, tests_text: str, all_text: str) -> dict:
    rel=str(path.relative_to(ROOT))
    defs=py_defs(path)
    placeholder=bool(PLACEHOLDER_RX.search(text))
    has_argparse='argparse' in text
    reads=bool(re.search(r'read_text|json\.loads|open\(|subprocess\.run|yaml\.safe_load', text))
    writes=bool(re.search(r'write_text|json\.dump|print\(', text))
    called=(all_text.count(rel) + all_text.count(path.name)) > (1 if rel.endswith('.py') else 0)
    tested=(rel in tests_text) or (path.stem in tests_text)
    schema=('jsonschema' in text or 'schema' in text.lower())
    evidence=('evidence' in text.lower())
    quality=('quality_gate' in text or 'quality' in text.lower())
    report=('report' in text.lower())
    status='usable'
    if path.suffix == '.md': status='paper-only'
    elif placeholder: status='partial'
    if not tested and rel.split('/')[0] not in {'scripts'}:
        status='partial' if status=='usable' else status
    lower_text = text.lower()
    audit_or_policy_file = rel.startswith('scripts/ultimate_') or rel in {'scripts/dashboard_evidence_selftest.py','scripts/round3_acceptance_selftest_fast.py','quality/quality_gate.py','tools/tool_registry.yaml'}
    if not audit_or_policy_file and ('placeholder' in lower_text or 'mock' in lower_text or 'fake' in lower_text):
        status='fake-ready' if path.suffix != '.md' else 'paper-only'
    if defs.get('syntax_ok') is False:
        status='blocker'
    claimed='executable helper' if path.suffix=='.py' else 'configuration/schema/documentation artifact'
    return {
      'file_path': rel,
      'claimed_capability': claimed,
      'actual_code_provides_capability': path.suffix in {'.py','.js','.go','.java','.rb','.php','.json','.yaml','.yml'} and defs.get('syntax_ok') is not False,
      'placeholder_or_fake_markers': PLACEHOLDER_RX.findall(text)[:10],
      'has_pass_todo_mock_stub_fake': placeholder,
      'reads_input': reads or has_argparse,
      'produces_output': writes,
      'called_by_other_module_or_script': called,
      'test_covered_by_name_or_path': tested,
      'schema_validation_visible': schema,
      'enters_evidence_manifest': evidence,
      'enters_quality_gate': quality,
      'enters_final_report': report,
      'python_functions': defs.get('functions', [])[:30],
      'python_classes': defs.get('classes', [])[:20],
      'status': status,
    }


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out', default=str(ROOT/'outputs/current/ultimate_fake_ready_audit.json')); ap.add_argument('--md', default=str(ROOT/'outputs/current/ultimate_fake_ready_audit.md'))
    ns=ap.parse_args()
    all_text='\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in core_files() if p.stat().st_size < 300000)
    tests_text='\n'.join(p.read_text(encoding='utf-8', errors='ignore') for p in (ROOT/'tests').rglob('*') if p.is_file() and p.stat().st_size < 300000)
    file_audits=[]
    for p in core_files():
        if p.stat().st_size > 500000: continue
        file_audits.append(classify(p, p.read_text(encoding='utf-8', errors='ignore'), tests_text, all_text))
    cap_rows=[]
    for name, paths, tests, declared in CAPABILITIES:
        existing=[x for x in paths if (ROOT/x).exists()]
        test_existing=[x for x in tests if (ROOT/x).exists()]
        status=declared
        if not existing: status='paper-only'
        elif not test_existing and declared not in {'paper-only','environment-dependent'}: status='unverified'
        cap_rows.append({'capability': name, 'paths': existing, 'tests': test_existing, 'status': status, 'fake_ready': status in {'paper-only','fake-ready','unverified'}})
    summary={k:sum(1 for f in file_audits if f['status']==k) for k in ['usable','partial','paper-only','fake-ready','blocker']}
    out={'schema_version':'ultimate-fake-ready-audit-v1','verdict':'candidate-only','summary':summary,'capabilities':cap_rows,'files':file_audits,
         'policy':'No dynamic manifest-backed evidence means severe findings remain candidate. Markdown-only and untested capabilities are not counted as usable.'}
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# Ultimate fake-ready audit','','总体判决：candidate-only','','## Capability truth table','','| Capability | Status | Paths | Tests |','|---|---|---|---|']
    for r in cap_rows:
        lines.append(f"| {r['capability']} | {r['status']} | `{', '.join(r['paths'])}` | `{', '.join(r['tests'])}` |")
    lines += ['','## Core file summary', json.dumps(summary,ensure_ascii=False)]
    Path(ns.md).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'verdict':out['verdict'],'files':len(file_audits),'summary':summary,'fake_ready_capabilities':sum(1 for c in cap_rows if c['fake_ready'])},ensure_ascii=False))

if __name__=='__main__': main()
