from __future__ import annotations
import http.server
import json
import shutil
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY_FIX = ROOT / 'tests' / 'fixtures' / 'key_gap_app'
MONO_FIX = ROOT / 'tests' / 'fixtures' / 'monorepo_workspace'
FP_FIX = ROOT / 'tests' / 'fixtures' / 'false_positive_negative'

def run(cmd, timeout=120):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)

def prepared_key_gap(tmp_path: Path) -> Path:
    dst = tmp_path / 'key_gap_app'
    shutil.copytree(KEY_FIX, dst, symlinks=False)
    target = tmp_path / 'outside-target.txt'
    target.write_text('outside scope', encoding='utf-8')
    link = dst / 'runtime-created-outside-symlink'
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError):
        # Platforms without symlink support still keep the marker test meaningful via coverage gate failure.
        pass
    return dst

def test_js_strict_ast_uses_real_parser_and_returns_zero():
    proc = run(['node', 'scripts/js-ast-endpoint-extractor.mjs', str(KEY_FIX), '--strict-ast'])
    assert proc.returncode == 0, proc.stderr
    rows = [json.loads(x) for x in proc.stdout.splitlines() if x.strip()]
    assert rows
    assert all(r['parser_mode'].endswith('_ast_walk') for r in rows)
    assert not any(r['parser_mode'] == 'lexical_fallback' for r in rows)

def test_runtime_schema_and_manifest_merge_can_create_confirmed_with_qg(tmp_path):
    import importlib.util
    import sys as _sys
    from jsonschema import Draft202012Validator
    manifest = tmp_path / 'static-manifest.json'
    source = tmp_path / 'app.py'
    source.write_text('route /api/ping', encoding='utf-8')
    def ev(n, section, typ='coverage_anchor', value=None):
        return {'evidence_id':f'ev-{n:08d}','collector_name':'test','skill_name':'Info-End','source_file':str(source),'source_line_start':1,'source_line_end':1,'source_type':'source','discovered_item_type':typ,'discovered_item_value_redacted':value or {'section':section},'raw_value_hash':str(n%10)*64,'confidence':.8,'severity_hint':'info','auth_relevance':'unknown','tenant_relevance':'unknown','role_relevance':'unknown','endpoint_relevance':'high' if section == 'route-api-inventory' else 'unknown','data_sensitivity':'unknown','reproduction_hint':'test','collection_time':'2026-01-01T00:00:00+00:00','scope_id':'test','false_positive_reason':'','needs_human_review':True,'linked_report_section':section,'path':str(source),'redaction_status':'not_sensitive_or_no_secret_literal','collector_provenance':{},'finding_status':'candidate','reason':'test candidate evidence','raw_evidence_hash':str(n%10)*64,'redacted_evidence':value or {'section':section},'reproduction_command':'test','limitation':'test limitation'}
    items=[ev(1,'authorization-scope'), ev(2,'project-fingerprint'), ev(3,'technology-stack'), ev(4,'route-api-inventory','endpoint',{'method':'GET','route':'/api/ping'}), ev(5,'frontend-js'), ev(6,'configuration-deployment'), ev(7,'dependency-surface'), ev(8,'evidence-index')]
    manifest.write_text(json.dumps({'schema_version':'1.0','project':{'name':'x','root':str(tmp_path),'base_urls':[]},'generated_at':'2026-01-01T00:00:00+00:00','items':items}), encoding='utf-8')
    runtime = tmp_path / 'runtime-evidence.json'
    runtime_obj = {
        'schema_version':'runtime-evidence.v1', 'run_id':'runtime-test', 'mode':'local_loopback_safe_probe',
        'playwright_available':False, 'scope_id':'test', 'generated_at':'2026-01-01T00:00:00+00:00', 'status':'PASS',
        'records':[{'role_context':'unspecified_local_probe','tenant_context':'unspecified_local_probe','url':'http://127.0.0.1:1/api/ping','method':'GET','capture_status':'captured','request_sample':{'safe_method_only':True,'source_evidence_id':'ev-00000004','route':'/api/ping'},'response_sample':{'status_code':200,'body_hash':'0'*64,'headers_sample':{}},'screenshot':None,'har_entry':None,'safety':'local_loopback_only; safe HTTP methods only; no auth bypass; no third-party targets','source_evidence_id':'ev-00000004','source_file':str(source),'source_line_start':1,'finding_status':'confirmed','confidence':0.95,'reason':'confirmed runtime evidence from authorized loopback probe','limitation':'Only safe-method loopback probing is performed; no destructive actions, no third-party targets, no auth bypass attempts.'}]
    }
    runtime.write_text(json.dumps(runtime_obj), encoding='utf-8')
    schema=json.loads((ROOT/'schemas/runtime-evidence.schema.json').read_text())
    assert not list(Draft202012Validator(schema).iter_errors(runtime_obj))
    _sys.path.insert(0, str(ROOT/'scripts'))
    spec=importlib.util.spec_from_file_location('emb', ROOT/'scripts/evidence_manifest_builder.py')
    emb=importlib.util.module_from_spec(spec); spec.loader.exec_module(emb)
    rows, prov = emb.load_items(runtime)
    runtime_item = emb.normalize_item(rows[0], 0, prov, 'test')
    assert runtime_item['discovered_item_type'] == 'runtime_endpoint_validation'
    assert runtime_item['finding_status'] == 'confirmed'
    merged = tmp_path / 'merged-manifest.json'
    merged.write_text(json.dumps({'schema_version':'1.0','project':{'name':'x','root':str(tmp_path),'base_urls':[]},'generated_at':'2026-01-01T00:00:00+00:00','items':items+[runtime_item]}), encoding='utf-8')
    _sys.path.insert(0, str(ROOT/'quality'))
    import _quality_core
    q = _quality_core.unified(str(tmp_path), str(tmp_path), str(merged))
    assert q['status'] == 'PASS'
    spec2=importlib.util.spec_from_file_location('ldv', ROOT/'runtime/local_dynamic_validator.py')
    ldv=importlib.util.module_from_spec(spec2); spec2.loader.exec_module(ldv)
    assert not ldv.is_local_url('https://example.com')



def test_coverage_gate_requires_declared_skipped_reasons(tmp_path):
    import sys as _sys
    _sys.path.insert(0, str(ROOT/'scripts'))
    _sys.path.insert(0, str(ROOT/'quality'))
    from _info_collect_lib import parse_scope, scan_inventory
    import _quality_core
    fix = tmp_path / 'fixture'
    fix.mkdir()
    (fix / 'ok.js').write_text("fetch('/api/ping')", encoding='utf-8')
    (fix / 'binary.bin').write_bytes(b'abc\x00def')
    (fix / 'huge.txt').write_text('a' * 2100000, encoding='utf-8')
    outside = tmp_path / 'outside.txt'
    outside.write_text('outside', encoding='utf-8')
    try:
        (fix / 'outside-symlink').symlink_to(outside)
    except (OSError, NotImplementedError):
        pass
    (fix / '.info-end-expected-skips.json').write_text(json.dumps({'required_skipped_reasons':['binary_file','large_file_over_2mb'] + (['symlink_skipped'] if (fix/'outside-symlink').is_symlink() else [])}), encoding='utf-8')
    scope=parse_scope(str(fix), fix)
    inv=scan_inventory(fix, scope, max_files=100, timeout=10, scan_profile='standard', follow_symlinks=False)
    assert inv['skipped_reasons'].get('binary_file', 0) >= 1
    assert inv['skipped_reasons'].get('large_file_over_2mb', 0) >= 1
    if (fix / 'outside-symlink').is_symlink():
        assert inv['skipped_reasons'].get('symlink_skipped', 0) >= 1
    manifest = tmp_path / 'manifest.json'
    def item(n, section):
        return {'evidence_id':f'ev-{n:08d}','collector_name':'test','source_file':str(fix/'ok.js'),'source_line_start':1,'source_line_end':1,'discovered_item_type':'coverage_anchor','discovered_item_value_redacted':{'section':section},'raw_value_hash':str(n%10)*64,'confidence':.8,'reason':'test','raw_evidence_hash':str(n%10)*64,'redacted_evidence':{'section':section},'reproduction_command':'test','limitation':'test','finding_status':'candidate','collection_time':'2026-01-01T00:00:00+00:00','scope_id':'test','linked_report_section':section,'redaction_status':'not_sensitive_or_no_secret_literal'}
    sections=['authorization-scope','project-fingerprint','technology-stack','route-api-inventory','frontend-js','configuration-deployment','dependency-surface','evidence-index']
    manifest.write_text(json.dumps({'schema_version':'1.0','project':{'name':'fixture','root':str(fix),'base_urls':[]},'generated_at':'2026-01-01T00:00:00+00:00','items':[item(i+1, s) for i,s in enumerate(sections)]}), encoding='utf-8')
    q=_quality_core.coverage_gate(str(manifest), str(fix), str(fix))
    assert q['status'] == 'PASS'
    assert not q['coverage']['missing_required_skipped_reasons']


def test_all_analyzers_have_contract_tests(tmp_path):
    import sys as _sys
    from jsonschema import Draft202012Validator
    _sys.path.insert(0, str(ROOT/'analyzers'))
    import _analyzer_core
    schema=json.loads((ROOT/'schemas/analyzer-output.schema.json').read_text())
    validator=Draft202012Validator(schema)
    sample_items=[
        {'evidence_id':'ev-aaaaaaa1','linked_report_section':'project-fingerprint','discovered_item_type':'language_detected','discovered_item_value_redacted':{'language':'TypeScript'},'tenant_relevance':'low','role_relevance':'low','auth_relevance':'low','finding_status':'candidate','source_file':'app.ts','reason':'x','limitation':'x'},
        {'evidence_id':'ev-aaaaaaa2','linked_report_section':'technology-stack','discovered_item_type':'framework_detected','discovered_item_value_redacted':'Express','tenant_relevance':'low','role_relevance':'low','auth_relevance':'low','finding_status':'candidate','source_file':'package.json','reason':'x','limitation':'x'},
        {'evidence_id':'ev-aaaaaaa3','linked_report_section':'route-api-inventory','discovered_item_type':'endpoint','discovered_item_value_redacted':{'method':'GET','route':'/api/tenant/settings'},'tenant_relevance':'medium','role_relevance':'medium','auth_relevance':'medium','finding_status':'candidate','source_file':'server.js','reason':'x','limitation':'x'},
        {'evidence_id':'ev-aaaaaaa4','linked_report_section':'frontend-js','discovered_item_type':'js_callgraph_api_call','discovered_item_value_redacted':{'resolved_endpoint':'/api/tenant/settings','method':'GET'},'tenant_relevance':'medium','role_relevance':'low','auth_relevance':'medium','finding_status':'candidate','source_file':'app.js','reason':'x','limitation':'x'},
        {'evidence_id':'ev-aaaaaaa5','linked_report_section':'parameter-dataflow','discovered_item_type':'parameter','discovered_item_value_redacted':{'name':'tenantId','route_binding':{'route':'/api/tenant/settings'}},'tenant_relevance':'medium','role_relevance':'low','auth_relevance':'low','finding_status':'candidate','source_file':'dto.ts','reason':'x','limitation':'x'},
        {'evidence_id':'ev-aaaaaaa6','linked_report_section':'configuration-deployment','discovered_item_type':'secret_name_signal','discovered_item_value_redacted':{'token':'****#abc'},'tenant_relevance':'low','role_relevance':'low','auth_relevance':'medium','redaction_status':'redacted','finding_status':'candidate','source_file':'.env.example','reason':'x','limitation':'x'},
    ]
    for analyzer, func in _analyzer_core.ANALYZERS.items():
        findings=func(sample_items)
        report={'schema_version':'info-end-analyzer-output.v1','generated_at':'2026-01-01T00:00:00+00:00','finding_count':len(findings),'findings':findings}
        assert not list(validator.iter_errors(report)), analyzer


def test_monorepo_workspace_fixture_detected(tmp_path):
    out = tmp_path / 'fingerprint.json'
    proc = run([sys.executable, 'scripts/project_fingerprint.py', '--input', str(MONO_FIX), '--scope', str(MONO_FIX), '--output', str(out), '--max-files', '200'])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    items = json.loads(out.read_text())['items']
    assert any(i['discovered_item_type'] == 'project_topology_detected' and 'monorepo_workspace' in i['discovered_item_value_redacted']['topologies'] for i in items)

def test_false_positive_fixtures_stay_candidate_not_confirmed(tmp_path):
    outputs=[]
    for collector in ['route_collector','docs_collector','js_asset_collector']:
        out = tmp_path / f'{collector}.json'
        proc = run([sys.executable, f'collectors/{collector}.py', '--input', str(FP_FIX), '--scope', str(FP_FIX), '--output', str(out), '--max-files', '100'])
        assert proc.returncode == 0, proc.stdout + proc.stderr
        outputs.append(out)
    merged = tmp_path / 'manifest.json'
    cmd=[sys.executable, 'scripts/evidence_manifest_builder.py', '--input', str(FP_FIX), '--scope', str(FP_FIX), '--output', str(merged)]
    for out in outputs:
        cmd += ['--collector-output', str(out)]
    proc = run(cmd)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    m = json.loads(merged.read_text())
    stale = [i for i in m['items'] if '/api/deprecated-admin' in json.dumps(i.get('discovered_item_value_redacted'), ensure_ascii=False) or '/api/comment-only' in json.dumps(i.get('discovered_item_value_redacted'), ensure_ascii=False) or '/api/dead-code-only' in json.dumps(i.get('discovered_item_value_redacted'), ensure_ascii=False) or '/api/mock-only' in json.dumps(i.get('discovered_item_value_redacted'), ensure_ascii=False)]
    assert stale
    assert all(i['finding_status'] == 'candidate' for i in stale)
    assert all(i['needs_human_review'] or 'static' in i.get('limitation','').lower() or 'literal' in i.get('limitation','').lower() for i in stale)
