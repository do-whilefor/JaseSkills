#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
JS={'.js','.mjs','.cjs','.jsx','.ts','.tsx'}
BACK={'.js','.ts','.tsx','.py','.java','.php','.go','.rs','.rb','.cs'}
ZOD=re.compile(r'''\b([A-Za-z_$][\w$]*)\s*=\s*z\.object\s*\(\s*\{(?P<body>[\s\S]{0,5000}?)\}\s*\)''')
YUP=re.compile(r'''\b([A-Za-z_$][\w$]*)\s*=\s*yup\.object\s*\(\s*\{(?P<body>[\s\S]{0,5000}?)\}\s*\)''')
JOI=re.compile(r'''\b([A-Za-z_$][\w$]*)\s*=\s*Joi\.object\s*\(\s*\{(?P<body>[\s\S]{0,5000}?)\}\s*\)''')
FIELD=re.compile(r'''([A-Za-z_$][\w$]{1,80})\s*[:=]''')
DTO=re.compile(r'''(?:class|interface|type)\s+([A-Za-z_$][\w$]*(?:Dto|DTO|Request|Payload|Input|Model)?)[\s\S]{0,4000}?[\{=]([\s\S]{0,4000}?)[\}\n];?''')

def rel(p,r):
    try: return str(p.resolve().relative_to(r.resolve())).replace('\\','/')
    except Exception: return str(p)

def fields(body):
    out=[]
    for m in FIELD.finditer(body or ''):
        k=m.group(1)
        if k not in {'return','const','let','var','function','if','for','while','switch'} and k not in out: out.append(k)
    return out

def scan_openapi(p):
    try: obj=json.loads(p.read_text(encoding='utf-8'))
    except Exception: return []
    out=[]
    for path,ops in (obj.get('paths') or {}).items():
        if isinstance(ops,dict):
            for meth,op in ops.items():
                params=[x.get('name') for x in op.get('parameters',[]) if isinstance(x,dict)] if isinstance(op,dict) else []
                out.append({'source':'openapi','path':path,'method':meth.upper(),'fields':[x for x in params if x]})
    return out

def main():
    ap=argparse.ArgumentParser(description='Align OpenAPI/Postman/zod/yup/joi/DTO/model fields with JS API parameter model.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--api-model', default='')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    schemas=[]
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rp=rel(p,root); low=p.name.lower()
        if low.endswith(('.openapi.json','swagger.json')) or low in {'openapi.json','swagger.json'}:
            schemas += [{'file':rp, **x} for x in scan_openapi(p)]
        if p.suffix.lower() in JS|BACK:
            text=p.read_text(encoding='utf-8', errors='replace')
            for rgx,typ in [(ZOD,'zod'),(YUP,'yup'),(JOI,'joi')]:
                for m in rgx.finditer(text): schemas.append({'source':typ,'file':rp,'name':m.group(1),'fields':fields(m.group('body')),'line':text.count('\n',0,m.start())+1})
            for m in DTO.finditer(text):
                fs=fields(m.group(2))
                if fs: schemas.append({'source':'dto-model','file':rp,'name':m.group(1),'fields':fs,'line':text.count('\n',0,m.start())+1})
    api={}
    if args.api_model and Path(args.api_model).exists():
        api=json.loads(Path(args.api_model).read_text(encoding='utf-8'))
    api_fields={p for a in api.get('apis',[]) for p in (a.get('body_params',[])+a.get('query_params',[])+a.get('path_params',[])+a.get('graphql_variables',[]))}
    schema_fields={f for s in schemas for f in s.get('fields',[])}
    hidden=sorted(schema_fields-api_fields)
    res={'schema_version':'js-schema-alignment/v1','status':'partial' if schemas else 'empty','schemas':schemas[:3000],'api_model_fields':sorted(api_fields),'schema_only_fields':hidden,'high_risk_schema_only_fields':[x for x in hidden if re.search(r'(role|admin|tenant|org|owner|user|quota|price|balance|status|state|force|debug|override|include|expand|fields)',x,re.I)],'downgrade':'schema-only fields are hidden-parameter candidates until backend acceptance is proven.'}
    (out/'js_schema_alignment.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'schemas':len(schemas),'schema_only_fields':len(hidden),'out':str(out/'js_schema_alignment.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()
