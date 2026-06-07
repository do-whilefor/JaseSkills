#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def simple_required(schema, data):
    errors=[]
    if schema.get('type')=='object' and not isinstance(data, dict): errors.append('root is not object')
    for k in schema.get('required',[]):
        if isinstance(data, dict) and k not in data: errors.append(f'missing required field: {k}')
    for k,prop in schema.get('properties',{}).items():
        if isinstance(data,dict) and k in data and 'const' in prop and data[k] != prop['const']:
            errors.append(f'{k} != const {prop["const"]}')
    return errors

def main():
    ap=argparse.ArgumentParser(description='Validate JSON artifacts against bundled schemas; uses jsonschema when installed, otherwise strict required/const fallback.')
    ap.add_argument('--schema', required=True)
    ap.add_argument('--input', required=True)
    args=ap.parse_args(); schema=json.loads(Path(args.schema).read_text(encoding='utf-8')); data=json.loads(Path(args.input).read_text(encoding='utf-8'))
    errors=[]; engine='fallback'
    try:
        import jsonschema
        jsonschema.Draft202012Validator(schema).validate(data)
        engine='jsonschema'
    except ImportError:
        errors=simple_required(schema, data)
    except Exception as e:
        errors=[str(e)]
    res={'ok':not errors,'engine':engine,'schema':args.schema,'input':args.input,'errors':errors}
    print(json.dumps(res, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 1)
if __name__=='__main__': main()
