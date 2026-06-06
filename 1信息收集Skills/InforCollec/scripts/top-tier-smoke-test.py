#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/'tests/fixtures/top_tier_info_app'

def run(script, *extra):
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'out.json'
        cmd=[sys.executable, str(ROOT/'scripts'/script), '--input', str(APP), '--scope', str(APP), '--output', str(out), '--format','json','--no-network','--redact-secrets','--max-files','2000','--timeout','20', *extra]
        subprocess.run(cmd,cwd=ROOT,check=True,text=True,capture_output=True,timeout=45)
        return json.loads(out.read_text(encoding='utf-8'))

def main():
    scope=run('scope_guard.py')
    fp=run('project_fingerprint.py')
    route=run('route_api_extractor.py')
    auth=run('auth_boundary_collector.py')
    conf=run('config_secret_signal_collector.py')
    js=run('js_deep_info_collector.py')
    hid=run('hidden_info_collector.py')
    dep=run('dependency_surface_collector.py')
    blob='\n'.join(json.dumps(x,ensure_ascii=False) for x in [scope,fp,route,auth,conf,js,hid,dep])
    required=['authorized_scope_confirmed','language_detected','framework_detected','openapi_path_operation','grpc_rpc_method','authorization_middleware','secret_name_signal','source_map_artifact','comment_hidden_info','dangerous_package_script']
    missing=[x for x in required if x not in blob]
    if 'ChangeMe123' in blob or 'SuperSecretValue123' in blob:
        raise SystemExit('secret redaction failed')
    if missing:
        raise SystemExit('missing smoke signals: '+','.join(missing))
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); route_out=td/'route.json'; hid_out=td/'hidden.json'; manifest=td/'manifest.json'; graph=td/'graph.json'; qg=td/'qg.json'; queue=td/'queue.json'
        for script,out in [('route_api_extractor.py',route_out),('hidden_info_collector.py',hid_out)]:
            subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--input',str(APP),'--scope',str(APP),'--output',str(out),'--format','json'],cwd=ROOT,check=True,timeout=45)
        subprocess.run([sys.executable,str(ROOT/'scripts/evidence_manifest_builder.py'),'--input',str(APP),'--scope',str(APP),'--output',str(manifest),'--format','json','--collector-output',str(route_out),'--collector-output',str(hid_out)],cwd=ROOT,check=True,timeout=45)
        subprocess.run([sys.executable,str(ROOT/'scripts/attack_surface_graph_builder.py'),'--input',str(manifest),'--scope',str(manifest),'--output',str(graph),'--format','json'],cwd=ROOT,check=True,timeout=45)
        subprocess.run([sys.executable,str(ROOT/'scripts/human_review_queue.py'),'--input',str(manifest),'--scope',str(manifest),'--output',str(queue),'--format','json'],cwd=ROOT,check=True,timeout=45)
        subprocess.run([sys.executable,str(ROOT/'scripts/info_quality_gate.py'),'--input',str(manifest),'--scope',str(manifest),'--output',str(qg),'--format','json','--min-score','40'],cwd=ROOT,check=True,timeout=45)
        assert json.loads(manifest.read_text())['items']
        assert json.loads(graph.read_text())['nodes']
        assert json.loads(queue.read_text())['count'] > 0
    print(json.dumps({'status':'PASS','fixture':str(APP),'checked':required},ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__':
    raise SystemExit(main())
