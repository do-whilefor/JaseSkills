#!/usr/bin/env python3
import json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs'; OUT.mkdir(exist_ok=True); checks=[]
def cmd(name,args):
    if not shutil.which(args[0]): checks.append({'id':name,'status':'missing','reason':args[0]+' not in PATH'}); return
    try:
        r=subprocess.run(args, text=True, capture_output=True, timeout=10); checks.append({'id':name,'status':'ready' if r.returncode==0 else 'failed','returncode':r.returncode,'stdout':r.stdout[:300],'stderr':r.stderr[:300]})
    except Exception as e: checks.append({'id':name,'status':'failed','reason':str(e)})
for name,args in [('node',['node','--version']),('npm',['npm','--version']),('python',[sys.executable,'--version']),('java',['java','-version']),('php',['php','-v']),('ruby',['ruby','-v']),('go',['go','version']),('cargo',['cargo','--version'])]: cmd(name,args)
for mod in ['playwright','tree_sitter','libcst']:
    r=subprocess.run([sys.executable,'-c',f'import {mod}'], text=True, capture_output=True); checks.append({'id':'python_module_'+mod,'status':'ready' if r.returncode==0 else 'missing','stderr':r.stderr[:200]})
if shutil.which('node'):
    script="for (const m of ['@babel/parser','@babel/traverse','typescript']) { try { require(m); console.log(m+':ready') } catch(e) { console.log(m+':missing') } }"
    r=subprocess.run(['node','-e',script], text=True, capture_output=True)
    for line in r.stdout.splitlines():
        if ':' in line:
            k,s=line.split(':',1); checks.append({'id':'node_module_'+k,'status':s})
ready=sum(1 for c in checks if c['status']=='ready'); total=len(checks)
out={'status':'ready' if ready==total else 'degraded','ready':ready,'total':total,'checks':checks,'policy':'Only ready checks may be used as real integrations.'}
(OUT/'toolchain_strict_verify.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2)); raise SystemExit(0 if out['status']=='ready' else 1)
