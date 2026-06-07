#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from collectors.js_asset_collector import collect as collect_js
from js.chunk_lineage_builder import build as build_lineage
from js.sourcemap_restorer import restore as restore_map

def run(root: str | Path, out_dir: str | Path) -> dict:
    root=Path(root).resolve(); out_dir=Path(out_dir).resolve(); out_dir.mkdir(parents=True,exist_ok=True)
    assets=collect_js(root)
    lineage=build_lineage(root, out_dir/'chunk_lineage.json')
    restored=[]
    for sm in assets.get('sourcemaps',[]):
        f=root/sm.get('file','')
        if f.exists():
            try:
                restored.append(restore(map_file=f if f.suffix=='.map' else None, js_file=None if f.suffix=='.map' else f, out_dir=out_dir/'restored_sources'))
            except Exception as e:
                restored.append({'status':'failed','file':sm.get('file'),'error':str(e)})
    data={'schema_version':'js-deep-audit-v1','assets':assets,'chunk_lineage':lineage,'sourcemap_restoration':restored,'api_parameter_permission_evidence':{'endpoints':assets.get('endpoints',[]),'parameters':assets.get('hidden_parameters',[]),'role_permission_constants':assets.get('role_permission_constants',[]),'evidence_policy':'candidate_only_until_backend_and_dynamic_replay'}}
    (out_dir/'js_deep_audit.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return data

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--out-dir',required=True); ns=ap.parse_args(); data=run(ns.root,ns.out_dir); print(json.dumps({'endpoints':len(data['assets'].get('endpoints',[])),'chunks':data['chunk_lineage']['counts']['chunks'],'restored_maps':len(data['sourcemap_restoration'])},ensure_ascii=False))
if __name__=='__main__': main()
