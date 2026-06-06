#!/usr/bin/env python3
"""Runtime readiness checker for the Skills package.

It checks local tool availability and safe scope defaults. It does not start
services, install browsers, or probe external hosts.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path

def tool(name, args=None):
    exe=shutil.which(name)
    if not exe: return {'available':False,'reason':'not_on_path'}
    if not args: return {'available':True,'path':exe}
    try:
        r=subprocess.run([name]+args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=5)
        return {'available':r.returncode==0,'path':exe,'returncode':r.returncode,'version':(r.stdout or '').strip().split('\n')[0][:200]}
    except Exception as e: return {'available':False,'path':exe,'reason':type(e).__name__+': '+str(e)}

def main():
    ap=argparse.ArgumentParser(description='Check local runtime readiness without installing or probing targets.')
    ap.add_argument('--project-root', default='.')
    ap.add_argument('--base-url', action='append', default=[])
    ap.add_argument('--out', default=None)
    args=ap.parse_args(); root=Path(args.project_root).resolve()
    urls=[]
    for u in args.base_url:
        ok=u.startswith(('http://localhost','http://127.0.0.1','https://localhost','https://127.0.0.1'))
        urls.append({'url':u,'default_local_allowed':ok,'note':'Non-local hosts require explicit written authorization and allow-host flags.' if not ok else 'local default allowed'})
    checks={
      'python3': tool('python3',['--version']),
      'node': tool('node',['--version']),
      'npm': tool('npm',['--version']),
      'curl': tool('curl',['--version']),
      'jq': tool('jq',['--version']),
      'git': tool('git',['--version']),
      'docker': tool('docker',['--version']),
      'bash': tool('bash',['--version']),
      'playwright_import': {'available': False, 'reason':'checked by parser-backend-check.py as playwright_node'},
      'burp_proxy_env': {'available': bool(os.environ.get('BURP_PROXY') or os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')), 'note':'Presence only; not proof that Burp is running or authorized.'}
    }
    required_files=['README.md','CAPABILITY_INDEX.md','schemas/evidence-manifest.schema.json','schemas/asset-ledger.schema.json','schemas/info-surface.schema.json','schemas/runtime-evidence.schema.json','schemas/finding-evidence-chain.schema.json','scripts/quality-gate-check.py','scripts/qg-jsonl-score.py','scripts/report-to-manifest.py','scripts/js-ast-endpoint-extractor.mjs','scripts/codegraph-builder.py','scripts/source-sink-dataflow.py','scripts/playwright-har-role-matrix.mjs','scripts/ws-readonly-capture.mjs','detectors/c01_c05_access_control.py','dashboard/dashboard_generator.py']
    file_checks={f:(root/f).exists() for f in required_files}
    report={'schema_version':'package-schema','generated_at':datetime.now(timezone.utc).isoformat(),'project_root':str(root),'base_url_checks':urls,'tool_checks':checks,'required_package_files':file_checks,'status':'PASS' if all(file_checks.values()) else 'FAIL'}
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).write_text(text,encoding='utf-8')
    print(text)
    return 0 if report['status']=='PASS' else 2
if __name__=='__main__': raise SystemExit(main())
