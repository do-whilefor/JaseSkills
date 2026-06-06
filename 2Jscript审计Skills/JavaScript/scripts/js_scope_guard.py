#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description='Validate authorization scope before any JS audit workflow is reportable.')
    ap.add_argument('--scope', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); scope=json.loads(Path(args.scope).read_text(encoding='utf-8'))
    errors=[]
    if scope.get('authorized_use') is not True: errors.append('authorized_use must be true')
    if scope.get('non_destructive') is not True: errors.append('non_destructive must be true')
    if not isinstance(scope.get('targets'), list) or not scope.get('targets'): errors.append('targets must be a non-empty list')
    if any(str(t).startswith(('http://','https://')) is False and not str(t).startswith('/') for t in scope.get('targets',[])): errors.append('target must be URL or local path')
    out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    res={'schema_version':'js-scope-guard/v1','ok':not errors,'scope':scope,'errors':errors}
    (out/'js_scope_guard.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(res, ensure_ascii=False, indent=2))
    raise SystemExit(0 if not errors else 2)
if __name__=='__main__': main()
