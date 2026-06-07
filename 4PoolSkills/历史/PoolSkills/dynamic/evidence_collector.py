#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime, hashlib, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from common.scope_guard import redact_text, contains_unredacted_secret, sha256_file

DYNAMIC_KEYS = ['request_ref','response_ref','screenshot_ref','trace_ref','har_ref','console_ref','dom_ref']

def now():
    return datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')

def _rel_or_none(p: Path, root: Path) -> str | None:
    try:
        rp=p.resolve(); rr=root.resolve()
        if rp == rr or rr in rp.parents:
            return str(rp.relative_to(rr)).replace('\\','/')
    except Exception:
        pass
    return None

def _resolve_ref(root: Path, ref: str | None) -> Path | None:
    if not ref:
        return None
    p = Path(ref)
    rp = p.resolve() if p.is_absolute() else (root / p).resolve()
    rr = root.resolve()
    if not (rp == rr or rr in rp.parents):
        return None
    if not rp.exists() or not rp.is_file() or rp.is_symlink():
        return None
    return rp

def _hash_refs(root: Path, r: dict) -> dict:
    hashes={}
    for k in DYNAMIC_KEYS:
        p=_resolve_ref(root, r.get(k))
        if p:
            hashes[k]=sha256_file(p)
    return hashes

def stitch_dynamic(manifest_file: str | Path, replay_file: str | Path, root: str | Path, command: str | None = None) -> dict:
    root=Path(root).resolve()
    manifest=json.loads(Path(manifest_file).read_text(encoding='utf-8'))
    replay=json.loads(Path(replay_file).read_text(encoding='utf-8'))
    raw_dir=root/'evidence'/'raw_dynamic'
    san_dir=root/'evidence'/'sanitized_dynamic'
    raw_dir.mkdir(parents=True,exist_ok=True)
    san_dir.mkdir(parents=True,exist_ok=True)
    existing={(e.get('related_finding'), e.get('type'), e.get('replay_plan_id')) for e in manifest.get('evidence',[])}
    stitched=0
    errors=[]
    for r in replay.get('results',[]):
        fid=r.get('finding_id')
        rp=r.get('replay_plan_id')
        readable_refs={}
        ref_errors=[]
        for k in DYNAMIC_KEYS:
            if r.get(k):
                p=_resolve_ref(root, r.get(k))
                if not p:
                    ref_errors.append(f'{k}:missing_or_out_of_scope:{r.get(k)}')
                else:
                    readable_refs[k]=_rel_or_none(p, root)
        if r.get('status') in {'passed','confirmed_non_destructive'} and ref_errors:
            errors.append({'finding_id':fid,'replay_plan_id':rp,'errors':ref_errors})
            continue
        if not readable_refs and r.get('status') not in {'passed','confirmed_non_destructive'}:
            manifest.setdefault('dynamic_stitching',{}).setdefault('skipped',[]).append({'finding_id':fid,'replay_plan_id':rp,'status':r.get('status'),'reason':'no_dynamic_artifacts'})
            continue
        key=(fid,'dynamic_replay',rp)
        if key in existing:
            continue
        eid='ev-dyn-'+hashlib.sha256(f'{fid}:{rp}:{json.dumps(readable_refs,sort_keys=True)}'.encode()).hexdigest()[:16]
        summary={
            'finding_id': fid,
            'replay_plan_id': rp,
            'status': r.get('status'),
            'role': r.get('role'),
            'tenant': r.get('tenant'),
            'negative_status': r.get('negative_status'),
            'blocked_status': r.get('blocked_status'),
            'refs': readable_refs,
            'artifact_hashes': _hash_refs(root, r),
            'errors': r.get('errors') or [],
            'stitched_at': now(),
        }
        raw_file=raw_dir/f'{eid}.json'
        san_file=san_dir/f'{eid}.json'
        raw_text=json.dumps(summary,ensure_ascii=False,indent=2)
        san_text, status=redact_text(raw_text)
        raw_file.write_text(raw_text+'\n',encoding='utf-8')
        san_file.write_text(san_text+'\n',encoding='utf-8')
        redaction_status='failed_unredacted_secret' if contains_unredacted_secret(san_text) else status
        ev={
            'evidence_id': eid,
            'type': 'dynamic_replay',
            'source_file': None,
            'source_tool': 'playwright_runner',
            'command': command or f'dynamic/evidence_collector.py --manifest {manifest_file} --replay {replay_file}',
            'timestamp': now(),
            'hash': hashlib.sha256(san_text.encode()).hexdigest(),
            'scope_status': 'in_scope_dynamic_artifacts' if not ref_errors else 'dynamic_artifact_ref_errors',
            'redaction_status': redaction_status,
            'raw_path': _rel_or_none(raw_file, root) or str(raw_file),
            'sanitized_path': _rel_or_none(san_file, root) or str(san_file),
            'related_finding': fid,
            'related_route': None,
            'related_role': r.get('role'),
            'related_tenant': r.get('tenant'),
            'replay_plan_id': rp,
        }
        for k in DYNAMIC_KEYS:
            ev[k]=readable_refs.get(k)
        manifest.setdefault('evidence',[]).append(ev)
        stitched+=1
    manifest.setdefault('dynamic_stitching',{})['stitched_at']=now()
    manifest['dynamic_stitching']['replay_file']=str(replay_file)
    manifest['dynamic_stitching']['stitched_dynamic_evidence']=stitched
    manifest['dynamic_stitching']['errors']=errors
    manifest['root']=str(root)
    return manifest

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--replay', required=True)
    ap.add_argument('--root', required=True)
    ap.add_argument('--command')
    ap.add_argument('--out', required=True)
    ns=ap.parse_args()
    try:
        data=stitch_dynamic(ns.manifest, ns.replay, ns.root, ns.command); code=0
    except Exception as e:
        data={'schema_version':'evidence-manifest-v1','status':'failed','error':str(e),'evidence':[]}; code=1
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True)
    Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':data.get('status','stitched'),'evidence':len(data.get('evidence',[])),'stitched':data.get('dynamic_stitching',{}).get('stitched_dynamic_evidence',0)},ensure_ascii=False))
    sys.exit(code)
if __name__=='__main__': main()
