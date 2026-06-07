#!/usr/bin/env python3
"""Build explicit manifest index. Fixture manifests are excluded unless --allow-fixtures."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest-dir', action='append', required=True); ap.add_argument('--allow-fixtures', action='store_true'); ap.add_argument('--out', required=True)
    a=ap.parse_args(); rows=[]
    for d in a.manifest_dir:
        for p in Path(d).rglob('*.json'):
            try: m=json.loads(p.read_text(encoding='utf-8', errors='ignore'))
            except Exception: continue
            if not isinstance(m,dict) or 'final_status' not in m or 'evidence_id' not in m: continue
            rel=str(p.resolve().relative_to(ROOT)) if p.resolve().is_relative_to(ROOT) else str(p)
            is_fixture='fixture' in rel.lower() or m.get('authorization_scope')=='local_authorized_fixture_only'
            if is_fixture and not a.allow_fixtures: continue
            rows.append({'path':rel,'sha256':sha(p),'fixture_allowed':bool(is_fixture and a.allow_fixtures),'final_status':m.get('final_status'),'evidence_id':m.get('evidence_id')})
    obj={'schema_version':'manifest_index_v1','source_policy':'explicit_manifest_index_only','manifests':rows}
    out=Path(a.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'ok':True,'count':len(rows),'out':str(out)}, ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
