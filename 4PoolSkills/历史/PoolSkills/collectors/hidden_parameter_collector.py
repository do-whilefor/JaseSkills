#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import iter_scoped_files, load_scope, read_text_scoped
RX=[('dto_validator',re.compile(r'(?:class\s+\w*(?:DTO|Dto|Request|Input)|z\.object|Joi\.object|Schema\(|pydantic|BaseModel|FormRequest)',re.I)),('orm_mass_assignment',re.compile(r'(?:fillable|guarded|Object\.assign|\.update\(|\.create\(|\.merge\(|request\.all\(|req\.body)',re.I)),('hidden_sensitive_param',re.compile(r'\b(?P<name>tenant_?id|org_?id|workspace_?id|role|roles|permission|isAdmin|admin|price|discount|status|state|owner_?id|user_?id)\b',re.I))]
def hid(*x): return 'param-'+hashlib.sha256(':'.join(map(str,x)).encode()).hexdigest()[:14]
def line(t,p): return t[:p].count('\n')+1
def collect(root, scope_file=None):
    root=Path(root).resolve(); scope=load_scope(root, scope_file); items=[]
    for p in iter_scoped_files(root, scope):
        if p.suffix.lower() not in {'.py','.js','.ts','.tsx','.java','.php','.rb','.go','.rs'}: continue
        text,_=read_text_scoped(p,root,scope,limit=1_000_000); rel=str(p.relative_to(root))
        context_tags=[name for name,rx in RX[:2] if rx.search(text)]
        for m in RX[2][1].finditer(text):
            items.append({'parameter_id':hid(rel,m.start()),'name':m.group('name'),'file':rel,'line':line(text,m.start()),'source_tags':context_tags or ['source_code'],'route_binding':'unresolved_until_semantic_graph','traceability':'file_line_and_context','risk_reason':'sensitive hidden or authority-bearing parameter'})
    return {'schema_version':'hidden-parameters-v1','root':str(root),'parameters':items,'counts':{'parameters':len(items)}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--scope-file'); ap.add_argument('--out',required=True); ns=ap.parse_args(); data=collect(ns.root,ns.scope_file); Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(data['counts'],ensure_ascii=False))
if __name__=='__main__': main()
