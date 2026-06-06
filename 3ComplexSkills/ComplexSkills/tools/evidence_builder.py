#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
def h(path):
    p=Path(path)
    if not p.exists() or not p.is_file(): return None
    return hashlib.sha256(p.read_bytes()).hexdigest()
def build(candidate_id, status, artifacts, source_locations=None, replay_id=None):
    arts=[]
    for item in artifacts or []:
        typ='file'; path=item if isinstance(item,str) else item.get('path'); typ=item.get('artifact_type','file') if isinstance(item,dict) else typ
        arts.append({'artifact_type':typ,'path':path,'sha256':h(path) or 'missing','redacted':False})
    return {'schema_version':'evidence_manifest_v1','manifest_id':f'manifest-{candidate_id}','candidate_id':candidate_id,'status':status,'scope':{'boundary':'local_authorized_or_fixture_only'},'source_locations':source_locations or [],'artifacts':arts,'replay_id':replay_id or 'manual_or_fixture','quality':{'pre_gate':'not_evaluated'},'report_mapping':{'section':'candidate_only_until_quality_gate_passes'}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--candidate-id',required=True); ap.add_argument('--status',default='STATIC_CANDIDATE'); ap.add_argument('--artifact',action='append',default=[]); ap.add_argument('--out'); args=ap.parse_args(); res=build(args.candidate_id,args.status,args.artifact); txt=json.dumps(res,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).parent.mkdir(parents=True, exist_ok=True); Path(args.out).write_text(txt+'\n',encoding='utf-8')
    print(txt)
if __name__=='__main__': main()
