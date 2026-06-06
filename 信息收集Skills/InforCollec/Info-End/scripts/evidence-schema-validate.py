#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from jsonschema import Draft202012Validator
from _info_collect_lib import find_unredacted_secrets

ROOT=Path(__file__).resolve().parents[1]
SCHEMAS={
  'evidence-manifest': ROOT/'schemas'/'evidence-manifest.schema.json',
  'asset-ledger': ROOT/'schemas'/'asset-ledger.schema.json',
  'runtime-evidence': ROOT/'schemas'/'runtime-evidence.schema.json',
  'finding-chain': ROOT/'schemas'/'finding-evidence-chain.schema.json',
}

def load(path:Path):
    return json.loads(path.read_text(encoding='utf-8', errors='ignore'))

def custom_evidence_checks(obj:dict) -> list[str]:
    errs=[]
    items=obj.get('items',[])
    seen=set()
    for i,it in enumerate(items if isinstance(items,list) else []):
        if not isinstance(it,dict):
            continue
        eid=it.get('evidence_id')
        if eid in seen: errs.append(f'items[{i}].evidence_id duplicate: {eid}')
        seen.add(eid)
        if isinstance(it.get('source_line_start'),int) and isinstance(it.get('source_line_end'),int) and it['source_line_end'] < it['source_line_start']:
            errs.append(f'items[{i}].source_line_end before source_line_start')
        secret_paths=find_unredacted_secrets(it.get('discovered_item_value_redacted'))
        if secret_paths:
            errs.append(f'items[{i}].discovered_item_value_redacted contains unredacted secret-like value at {secret_paths[:3]}')
        if it.get('redaction_status') == 'not_sensitive_or_no_secret_literal' and secret_paths:
            errs.append(f'items[{i}].redaction_status contradicts secret detector')
    return errs

def main():
    ap=argparse.ArgumentParser(description='Validate package JSON artifacts with real JSON Schema plus evidence-specific integrity checks.')
    ap.add_argument('file')
    ap.add_argument('--kind', choices=sorted(SCHEMAS), default='evidence-manifest')
    ap.add_argument('--schema', default=None, help='Optional explicit schema path')
    args=ap.parse_args(); path=Path(args.file)
    errs=[]
    try:
        obj=load(path)
    except Exception as e:
        print(json.dumps({'status':'FAIL','errors':[f'json_parse_error: {e}']},ensure_ascii=False,indent=2)); return 2
    schema_path=Path(args.schema) if args.schema else SCHEMAS[args.kind]
    try:
        schema=load(schema_path)
        validator=Draft202012Validator(schema)
        for e in sorted(validator.iter_errors(obj), key=lambda x: list(x.path)):
            loc='.'.join(str(p) for p in e.path) or '<root>'
            errs.append(f'{loc}: {e.message}')
    except Exception as e:
        errs.append(f'schema_validation_error: {e}')
    if args.kind=='evidence-manifest' and isinstance(obj,dict):
        errs += custom_evidence_checks(obj)
    result={'file':str(path),'kind':args.kind,'schema':str(schema_path),'status':'FAIL' if errs else 'PASS','errors':errs}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 2 if errs else 0
if __name__=='__main__': raise SystemExit(main())
