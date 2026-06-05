#!/usr/bin/env python3
"""Small evidence/asset schema validator using stdlib checks.

It intentionally avoids claiming full JSON Schema support unless a dedicated
validator is installed. Use it as a gate for required fields and obvious shape.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

REQ_MANIFEST={'schema_version':str,'project':dict,'items':list}
REQ_ITEM={'evidence_id':str,'kind':str,'path':str,'redaction_status':str}
REQ_ASSET_LEDGER={'schema_version':str}
REQ_RUNTIME_EVIDENCE={'schema_version':str,'run_id':str,'mode':str,'scope_id':str,'records':list}
REQ_FINDING_CHAIN={'candidate_vulnerability':str,'review_status':str,'source_file':str,'evidence':dict}

def load(path:Path):
    return json.loads(path.read_text(encoding='utf-8', errors='ignore'))

def check_type(obj, spec, prefix=''):
    errs=[]
    for k,t in spec.items():
        if k not in obj: errs.append(f'{prefix}{k}: missing')
        elif not isinstance(obj[k], t): errs.append(f'{prefix}{k}: expected {t.__name__}, got {type(obj[k]).__name__}')
    return errs

def main():
    ap=argparse.ArgumentParser(description='Validate evidence manifest or asset ledger required fields.')
    ap.add_argument('file'); ap.add_argument('--kind', choices=['evidence-manifest','asset-ledger','runtime-evidence','finding-chain'], default='evidence-manifest')
    args=ap.parse_args(); path=Path(args.file); errs=[]
    try: obj=load(path)
    except Exception as e:
        print(json.dumps({'status':'FAIL','errors':[f'json_parse_error: {e}']},ensure_ascii=False,indent=2)); return 2
    if args.kind=='evidence-manifest':
        errs += check_type(obj, REQ_MANIFEST)
        for i,it in enumerate(obj.get('items',[]) if isinstance(obj.get('items'),list) else []):
            if not isinstance(it,dict): errs.append(f'items[{i}]: expected object'); continue
            errs += check_type(it, REQ_ITEM, f'items[{i}].')
    elif args.kind=='asset-ledger':
        errs += check_type(obj, REQ_ASSET_LEDGER)
    elif args.kind=='runtime-evidence':
        errs += check_type(obj, REQ_RUNTIME_EVIDENCE)
        if obj.get('schema_version') != 'runtime-evidence.v1': errs.append('schema_version: expected runtime-evidence.v1')
        for i,it in enumerate(obj.get('records',[]) if isinstance(obj.get('records'),list) else []):
            if not isinstance(it,dict): errs.append(f'records[{i}]: expected object'); continue
            errs += check_type(it, {'role_context':str,'tenant_context':str,'url':str,'method':str,'capture_status':str,'safety':str}, f'records[{i}].')
    else:
        errs += check_type(obj, REQ_FINDING_CHAIN)
    print(json.dumps({'file':str(path),'kind':args.kind,'status':'FAIL' if errs else 'PASS','errors':errs},ensure_ascii=False,indent=2))
    return 2 if errs else 0
if __name__=='__main__': raise SystemExit(main())
