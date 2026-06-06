import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'tests/fixtures/top_tier_info_app'

def run(script,*extra,check=True):
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'out.json'
        cmd=[sys.executable, str(ROOT/'scripts'/script), '--input', str(APP), '--scope', str(APP), '--output', str(out), '--format', 'json', '--no-network', '--redact-secrets', '--max-files','2000','--timeout','20', *extra]
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        assert (p.returncode==0) if check else True, p.stderr+p.stdout
        return json.loads(out.read_text()) if out.exists() else json.loads(p.stdout)

def types(data): return {i.get('discovered_item_type') for i in data.get('items',[])}

def test_top_tier_scope_blocks_out_of_scope(tmp_path):
    scope=tmp_path/'scope.json'; allowed=tmp_path/'allowed'; denied=tmp_path/'denied'; allowed.mkdir(); denied.mkdir(); (denied/'x.txt').write_text('x')
    scope.write_text(json.dumps({'scope_id':'unit','allowed_roots':[str(allowed)],'denied_paths':[str(denied)]}))
    out=tmp_path/'out.json'
    p=subprocess.run([sys.executable, str(ROOT/'scripts/scope_guard.py'), '--input', str(denied/'x.txt'), '--scope', str(scope), '--output', str(out), '--format','json'], cwd=ROOT, text=True, capture_output=True)
    assert p.returncode != 0
    data=json.loads(out.read_text())
    assert data['items'][0]['discovered_item_type']=='out_of_scope_blocked'

def test_project_fingerprint_detects_languages_and_frameworks():
    data=run('project_fingerprint.py')
    blob=json.dumps(data,ensure_ascii=False)
    assert 'JavaScript' in blob and 'Python' in blob and 'Go' in blob and 'Rust' in blob
    assert 'Express' in blob and 'Next.js' in blob and 'FastAPI' in blob

def test_route_api_collector_detects_routes_specs_graphql_ws():
    data=run('route_api_extractor.py')
    ts=types(data)
    assert {'openapi_path_operation','graphql_schema_type','grpc_rpc_method','backend_or_frontend_route','literal_api_path_candidate','websocket_or_event_entry'} & ts
    blob=json.dumps(data,ensure_ascii=False)
    assert '/api/spec-only' in blob and 'ExportTenantAudit' in blob

def test_auth_config_js_hidden_dependency_collectors_redact():
    outputs=[run('auth_boundary_collector.py'),run('config_secret_signal_collector.py'),run('js_deep_info_collector.py'),run('hidden_info_collector.py'),run('dependency_surface_collector.py')]
    blob='\n'.join(json.dumps(x,ensure_ascii=False) for x in outputs)
    assert 'ChangeMe123' not in blob and 'SuperSecretValue123' not in blob
    for want in ['authorization_middleware','secret_name_signal','source_map_artifact','comment_hidden_info','dangerous_package_script']:
        assert want in blob

def test_top_tier_manifest_quality_graph_review_queue(tmp_path):
    route=tmp_path/'route.json'; hidden=tmp_path/'hidden.json'; manifest=tmp_path/'manifest.json'; qg=tmp_path/'qg.json'; graph=tmp_path/'graph.json'; queue=tmp_path/'queue.json'
    subprocess.run([sys.executable,str(ROOT/'scripts/route_api_extractor.py'),'--input',str(APP),'--scope',str(APP),'--output',str(route),'--format','json'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/hidden_info_collector.py'),'--input',str(APP),'--scope',str(APP),'--output',str(hidden),'--format','json'],cwd=ROOT,check=True)
    subprocess.run([sys.executable,str(ROOT/'scripts/evidence_manifest_builder.py'),'--input',str(APP),'--scope',str(APP),'--output',str(manifest),'--format','json','--collector-output',str(route),'--collector-output',str(hidden)],cwd=ROOT,check=True)
    m=json.loads(manifest.read_text())
    assert m['schema_version']=='1.0' and m['items']
    assert {'collector_name','skill_name','source_file','source_line_start','discovered_item_value_redacted','raw_value_hash','scope_id','needs_human_review'} <= set(m['items'][0])
    subprocess.run([sys.executable,str(ROOT/'scripts/attack_surface_graph_builder.py'),'--input',str(manifest),'--scope',str(manifest),'--output',str(graph),'--format','json'],cwd=ROOT,check=True)
    g=json.loads(graph.read_text()); assert g['nodes'] and g['edges']
    subprocess.run([sys.executable,str(ROOT/'scripts/human_review_queue.py'),'--input',str(manifest),'--scope',str(manifest),'--output',str(queue),'--format','json'],cwd=ROOT,check=True)
    assert json.loads(queue.read_text())['count'] > 0
    p=subprocess.run([sys.executable,str(ROOT/'scripts/info_quality_gate.py'),'--input',str(manifest),'--scope',str(manifest),'--output',str(qg),'--format','json','--min-score','40'],cwd=ROOT,text=True,capture_output=True)
    assert p.returncode==0, p.stderr+p.stdout
