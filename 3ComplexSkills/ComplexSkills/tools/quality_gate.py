#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
def evaluate(manifest):
    cid=manifest.get('candidate_id','unknown'); status=manifest.get('status','NOT_TESTED'); artifacts=manifest.get('artifacts') or []; sources=manifest.get('source_locations') or []; hard=[]; review=[]
    if status == 'DYNAMIC_CONFIRMED':
        if not sources: hard.append('confirmed_requires_source_location')
        if not artifacts: hard.append('confirmed_requires_request_response_or_equivalent_artifact')
        if not any(a.get('sha256') and a.get('sha256')!='missing' for a in artifacts): hard.append('confirmed_requires_existing_hashed_artifact')
    else: review.append(f'not_dynamic_confirmed:{status}')
    if manifest.get('scope',{}).get('boundary') not in {'local_authorized_or_fixture_only','local_authorized','fixture'}: hard.append('scope_boundary_missing_or_unsafe')
    passed=not hard and status=='DYNAMIC_CONFIRMED'; final='confirmed' if passed else ('needs_review' if review and not hard else 'blocked'); score=100 if passed else max(0,60-20*len(hard)-5*len(review))
    return {'schema_version':'quality_result_v1','candidate_id':cid,'passed':passed,'final_status':final,'hard_blocks':hard,'needs_review':review,'score':score,'report_allowed':passed}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('manifest'); ap.add_argument('--out'); args=ap.parse_args(); manifest=json.loads(Path(args.manifest).read_text(encoding='utf-8')); res=evaluate(manifest); txt=json.dumps(res,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).parent.mkdir(parents=True, exist_ok=True); Path(args.out).write_text(txt+'\n',encoding='utf-8')
    print(txt); return 0 if res['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
