from __future__ import annotations
import http.server
import json
import shutil
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests' / 'fixtures' / 'key_gap_app'

def make_symlink_fixture(tmp_path: Path) -> Path:
    dst = tmp_path / 'key_gap_app_symlink'
    shutil.copytree(FIX, dst, symlinks=False)
    target = tmp_path / 'outside.txt'
    target.write_text('outside scope', encoding='utf-8')
    try:
        (dst / 'runtime-created-outside-symlink').symlink_to(target)
    except (OSError, NotImplementedError):
        pass
    return dst

def run(cmd, timeout=90):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)

def load_items(path: Path):
    return json.loads(path.read_text())['items']

def test_js_wrapper_baseurl_callgraph_and_sourcemap(tmp_path):
    out=tmp_path/'js.json'
    proc=run([sys.executable,'collectors/js_asset_collector.py','--input',str(FIX),'--scope',str(FIX),'--output',str(out),'--max-files','100'])
    assert proc.returncode==0, proc.stderr
    items=load_items(out)
    types={i['discovered_item_type'] for i in items}
    assert 'js_http_client_wrapper' in types
    assert 'js_callgraph_api_call' in types
    assert any((i['discovered_item_value_redacted'].get('resolved_endpoint')=='/api/admin/users?include=roles&tenantId=t1') for i in items if i['discovered_item_type']=='js_callgraph_api_call')
    assert any('sourcemap' in json.dumps(i['discovered_item_value_redacted']) for i in items if i['discovered_item_type']=='js_callgraph_api_call')

def test_framework_route_extractors_have_non_unknown_handler_auth(tmp_path):
    out=tmp_path/'routes.json'
    proc=run([sys.executable,'collectors/route_collector.py','--input',str(FIX),'--scope',str(FIX),'--output',str(out),'--max-files','100'])
    assert proc.returncode==0, proc.stderr
    endpoints=[i['discovered_item_value_redacted'] for i in load_items(out) if i['discovered_item_type']=='endpoint']
    frameworks={e.get('framework') for e in endpoints if e.get('framework')}
    assert {'spring_boot','nestjs','fastapi_or_flask','rails','laravel','gin_echo_fiber'} <= frameworks
    assert all(e.get('handler') and e.get('handler') != 'unknown' for e in endpoints if e.get('framework'))
    assert any(e.get('authn')=='present' for e in endpoints)

def test_hidden_parameter_route_binding_and_models(tmp_path):
    out=tmp_path/'params.json'
    proc=run([sys.executable,'collectors/hidden_parameter_collector.py','--input',str(FIX),'--scope',str(FIX),'--output',str(out),'--max-files','100'])
    assert proc.returncode==0, proc.stderr
    vals=[i['discovered_item_value_redacted'] for i in load_items(out)]
    assert any(v.get('name')=='tenantId' and v.get('route_binding',{}).get('route') for v in vals if isinstance(v,dict))
    assert any(i['discovered_item_type']=='orm_or_mass_assignment_field' for i in load_items(out))

def test_dependency_local_cve_db_only_reports_verified_when_supplied(tmp_path):
    out1=tmp_path/'dep1.json'
    proc=run([sys.executable,'collectors/dependency_collector.py','--input',str(FIX),'--scope',str(FIX),'--output',str(out1),'--max-files','100'])
    assert proc.returncode==0
    assert not any(i['discovered_item_type']=='verified_dependency_advisory' for i in load_items(out1))
    out2=tmp_path/'dep2.json'
    proc=run([sys.executable,'collectors/dependency_collector.py','--input',str(FIX),'--scope',str(FIX),'--output',str(out2),'--max-files','100','--cve-db',str(FIX/'mock-cve-db.json')])
    assert proc.returncode==0, proc.stderr
    assert any(i['discovered_item_type']=='verified_dependency_advisory' and i.get('verification_status')=='verified' for i in load_items(out2))

def test_iac_resource_graph_and_coverage_skip_reasons(tmp_path):
    fix=make_symlink_fixture(tmp_path)
    out=tmp_path/'iac.json'
    proc=run([sys.executable,'collectors/iac_collector.py','--input',str(fix),'--scope',str(fix),'--output',str(out),'--max-files','100'])
    assert proc.returncode==0, proc.stderr
    assert any(i['discovered_item_type']=='iac_resource_graph' for i in load_items(out))
    # End-to-end quality gate exposes skipped binary/large/symlink reasons.
    pipe=tmp_path/'pipe'
    proc=run([sys.executable,'info_end_run.py','--input',str(fix),'--scope',str(fix),'--output',str(pipe),'--max-files','200','--cve-db',str(fix/'mock-cve-db.json')], timeout=180)
    assert proc.returncode==0, proc.stdout+proc.stderr
    q=json.loads((pipe/'unified-quality-gate.json').read_text())
    cov=[g for g in q['gates'] if g['gate']=='coverage_gate'][0]['coverage']
    reasons=cov['skipped_reasons']
    assert reasons.get('binary_file',0) >= 1
    assert reasons.get('large_file_over_2mb',0) >= 1
    if (fix/'runtime-created-outside-symlink').is_symlink():
        assert reasons.get('symlink_skipped',0) >= 1

def test_frontend_backend_correlation_and_role_tenant_matrix(tmp_path):
    pipe=tmp_path/'pipe'
    proc=run([sys.executable,'info_end_run.py','--input',str(FIX),'--scope',str(FIX),'--output',str(pipe),'--max-files','200','--cve-db',str(FIX/'mock-cve-db.json')], timeout=120)
    assert proc.returncode==0, proc.stdout+proc.stderr
    corr=json.loads((pipe/'frontend_backend_correlation_analyzer.json').read_text())
    metrics=corr['findings'][0]['correlation_metrics']
    assert metrics['route_to_api_correlation_accuracy'] > 0
    role=json.loads((pipe/'role_tenant_surface_analyzer.json').read_text())
    assert 'tenantId' in role['findings'][0]['boundary_fields']
    assert role['findings'][0]['permission_matrix_candidate']

def test_local_dynamic_validator_confirms_only_loopback_safe_method(tmp_path):
    manifest=tmp_path/'manifest.json'
    item={
      'evidence_id':'ev-x','collector_name':'test','skill_name':'Info-End','source_file':'dummy.py','source_line_start':1,'source_line_end':1,'source_type':'source','discovered_item_type':'endpoint','discovered_item_value_redacted':{'method':'GET','route':'/api/ping'},'raw_value_hash':'h','confidence':.8,'severity_hint':'info','auth_relevance':'unknown','tenant_relevance':'unknown','role_relevance':'unknown','endpoint_relevance':'high','data_sensitivity':'unknown','reproduction_hint':'','collection_time':'2026-01-01T00:00:00+00:00','scope_id':'test','false_positive_reason':'','needs_human_review':True,'linked_report_section':'route-api-inventory','path':'dummy.py','redaction_status':'not_sensitive_or_no_secret_literal','collector_provenance':{},'finding_status':'candidate','reason':'test','raw_evidence_hash':'h','redacted_evidence':{'method':'GET','route':'/api/ping'},'reproduction_command':'test','limitation':'test'
    }
    manifest.write_text(json.dumps({'project':{'root':str(tmp_path)},'items':[item]}))
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/api/ping': self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
            else: self.send_response(404); self.end_headers()
        def log_message(self, *args): pass
    srv=http.server.HTTPServer(('127.0.0.1',0), H)
    t=threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    try:
        out=tmp_path/'runtime.json'
        proc=run([sys.executable,'runtime/local_dynamic_validator.py','--manifest',str(manifest),'--base-url',f'http://127.0.0.1:{srv.server_port}','--output',str(out)])
        assert proc.returncode==0, proc.stderr
        data=json.loads(out.read_text())
        proc_schema=run([sys.executable,'scripts/evidence-schema-validate.py',str(out),'--kind','runtime-evidence'])
        assert proc_schema.returncode==0, proc_schema.stdout+proc_schema.stderr
        assert data['records'][0]['finding_status']=='confirmed'
        assert data['records'][0]['capture_status']=='captured'
        bad=tmp_path/'bad.json'
        proc=run([sys.executable,'runtime/local_dynamic_validator.py','--manifest',str(manifest),'--base-url','https://example.com','--output',str(bad)])
        assert proc.returncode != 0
    finally:
        srv.shutdown()
