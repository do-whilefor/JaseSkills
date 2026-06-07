#!/usr/bin/env python3
import argparse, json, shutil, socket, subprocess, sys, importlib.util
from pathlib import Path
COMMANDS=['python3','node','npm','npx','git','rg','go','cargo','java','mvn','php','composer','ruby','docker']
PY_MODULES=['jsonschema','yaml','libcst','tree_sitter']
NODE_PACKAGES=['typescript','@babel/parser','playwright','@playwright/test']
def cmd_exists(c): return shutil.which(c) is not None
def py_mod(m): return importlib.util.find_spec(m) is not None
def node_pkg(pkg):
    if not cmd_exists('node'): return False
    code=f"try{{require.resolve('{pkg}');process.exit(0)}}catch(e){{process.exit(1)}}"
    try: return subprocess.run(['node','-e',code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8).returncode==0
    except Exception: return False
def tcp(host,port):
    s=socket.socket(); s.settimeout(0.25)
    try: s.connect((host,port)); s.close(); return True
    except Exception: return False
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--out',required=True); ns=ap.parse_args()
    data={'schema_version':'runtime-readiness-v1','root':str(Path(ns.root).resolve()),'commands':{},'python_modules':{},'node_packages':{},'network_local':{},'claims':{},'overall_status':'ready'}
    for c in COMMANDS: data['commands'][c]=cmd_exists(c)
    for m in PY_MODULES: data['python_modules'][m]=py_mod(m)
    for p in NODE_PACKAGES: data['node_packages'][p]=node_pkg(p)
    data['network_local']['burp_proxy_127.0.0.1:8080']=tcp('127.0.0.1',8080)
    data['claims']={
      'ast_semantic_js':'ready' if data['node_packages'].get('@babel/parser') or data['node_packages'].get('typescript') else 'runtime_missing',
      'ast_semantic_python':'ready' if data['python_modules'].get('libcst') else 'degraded_to_ast_or_regex',
      'dynamic_playwright':'ready' if data['node_packages'].get('playwright') or data['node_packages'].get('@playwright/test') else 'runtime_missing',
      'burp_proxy':'ready' if data['network_local']['burp_proxy_127.0.0.1:8080'] else 'runtime_missing',
      'docker_target_start':'ready' if data['commands'].get('docker') else 'runtime_missing'
    }
    if any(v=='runtime_missing' for v in data['claims'].values()): data['overall_status']='degraded'
    Path(ns.out).parent.mkdir(parents=True, exist_ok=True); Path(ns.out).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'ok':True,'overall_status':data['overall_status'],'runtime_missing':[k for k,v in data['claims'].items() if v=='runtime_missing']}, ensure_ascii=False))
if __name__=='__main__': main()
