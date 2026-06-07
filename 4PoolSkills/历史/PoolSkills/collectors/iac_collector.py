#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import load_scope, iter_scoped_files, read_text_scoped
RULES=[('kubernetes_privileged',r'privileged:\s*true'),('kubernetes_hostpath',r'hostPath:'),('helm_debug_values',r'(debug|devMode):\s*true'),('terraform_public_ingress',r'0\.0\.0\.0/0'),('terraform_secret_literal',r'(?i)(password|secret|token)\s*=\s*"[^"]+"'),('docker_insecure',r'--privileged|SYS_ADMIN|:latest')]
def collect(root, scope_file=None):
    root=Path(root).resolve(); scope=load_scope(root,scope_file); items=[]
    for p in iter_scoped_files(root,scope,include_exts={'.yaml','.yml','.tf','.hcl','.json','.env','.Dockerfile',''}):
        text,_=read_text_scoped(p,root,scope,limit=1_000_000); rel=str(p.relative_to(root))
        for rid,rx in RULES:
            for m in re.finditer(rx,text,re.I):
                items.append({'id':'iac-'+hashlib.sha256(f'{rid}:{rel}:{m.start()}'.encode()).hexdigest()[:12],'rule_id':rid,'file':rel,'line':text[:m.start()].count('\n')+1,'status':'candidate','evidence':m.group(0)[:120]})
    return {'schema_version':'iac-inventory-v1','root':str(root),'findings':items,'counts':{'findings':len(items)}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--scope-file'); ap.add_argument('--out',required=True); ns=ap.parse_args(); data=collect(ns.root,ns.scope_file); Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(data['counts'],ensure_ascii=False))
if __name__=='__main__': main()
