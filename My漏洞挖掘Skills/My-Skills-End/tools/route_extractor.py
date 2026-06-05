#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, hashlib
from pathlib import Path
PATTERNS=[('express',re.compile(r'\b(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',re.I)),('fastapi',re.compile(r'@(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',re.I)),('django',re.compile(r'\bpath\s*\(\s*["\']([^"\']+)["\']',re.I)),('spring',re.compile(r'@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping)\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']',re.I)),('laravel',re.compile(r'Route::(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']',re.I))]
METHOD_MAP={'GetMapping':'GET','PostMapping':'POST','PutMapping':'PUT','PatchMapping':'PATCH','DeleteMapping':'DELETE','RequestMapping':'ANY'}
def sha256(p):
    try: return hashlib.sha256(p.read_bytes()).hexdigest()
    except Exception: return None
def line_no(text,pos): return text.count('\n',0,pos)+1
def rel(root,p):
    try: return str(p.relative_to(root))
    except Exception: return str(p)
def extract(root: Path):
    root=root.resolve(); out={'schema_version':'route_candidates_v1','parser_mode':'regex_candidate_not_ast','root':str(root),'routes':[],'warnings':['Routes are candidates unless confirmed by framework parser or dynamic replay.']}
    suffixes={'.js','.jsx','.ts','.tsx','.py','.java','.php','.rb','.go','.rs'}
    for p in sorted(x for x in root.rglob('*') if x.is_file() and x.suffix.lower() in suffixes):
        txt=p.read_text(encoding='utf-8', errors='ignore')
        for framework,rx in PATTERNS:
            for m in rx.finditer(txt):
                if framework in {'fastapi','django'}:
                    method='ANY' if framework=='django' else m.group(0).split('.')[1].split('(')[0].upper(); path=m.group(1)
                elif framework=='spring': method=METHOD_MAP.get(m.group(1),'ANY'); path=m.group(2)
                else: method=m.group(1).upper(); path=m.group(2)
                out['routes'].append({'method':method,'path':path,'framework_hint':framework,'handler':'unresolved_by_regex','source':{'path':rel(root,p),'line':line_no(txt,m.start()),'sha256':sha256(p)}})
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out'); args=ap.parse_args(); res=extract(Path(args.root)); txt=json.dumps(res,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).parent.mkdir(parents=True, exist_ok=True); Path(args.out).write_text(txt+'\n',encoding='utf-8')
    print(txt)
if __name__=='__main__': main()
