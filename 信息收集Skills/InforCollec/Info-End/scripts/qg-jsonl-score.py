#!/usr/bin/env python3
"""Evidence-chain quality gate for JSONL candidate/finding records.

This is a field-and-linkage gate, not a vulnerability confirmer. It rejects
confirmed/reportable/promoted records unless they carry source, evidence,
runtime validation, report linkage and, when --manifest is supplied, a manifest
item linkage by evidence_id or evidence.path.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

CONFIRMED={'confirmed','reportable','promoted'}
CANDIDATE={'candidate','needs_review','blocked','conflict','rejected'}

def read_jsonl(path):
    for idx,line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try: yield idx,json.loads(line)
        except json.JSONDecodeError as e: yield idx,{'_parse_error':str(e)}

def load_manifest(path):
    if not path: return None
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    ids={i.get('evidence_id') for i in data.get('items',[]) if i.get('evidence_id')}
    paths={str(i.get('path')) for i in data.get('items',[]) if i.get('path')}
    return {'ids':ids,'paths':paths,'raw':data}

def manifest_link_ok(r, manifest):
    if not manifest: return True, 'manifest_not_supplied'
    ev=r.get('evidence') if isinstance(r.get('evidence'),dict) else {}
    eid=ev.get('evidence_id') or r.get('evidence_id')
    epath=ev.get('path') or ev.get('evidence_path') or r.get('evidence_path')
    if eid and eid in manifest['ids']: return True, 'evidence_id'
    if epath and str(epath) in manifest['paths']: return True, 'evidence_path'
    return False, 'missing_manifest_linkage'

def score_record(r, manifest=None):
    errors=[]; warnings=[]
    if '_parse_error' in r: return {'status':'fail','errors':['invalid_json:'+r['_parse_error']], 'warnings':[]}
    status=str(r.get('review_status') or r.get('status') or '').lower()
    ev=r.get('evidence') if isinstance(r.get('evidence'),dict) else {}
    if not status: errors.append('missing_review_status')
    if not (r.get('source_file') or ev.get('source_file')): errors.append('missing_source_file')
    if not (r.get('source_line') or r.get('line') or ev.get('source_line')): warnings.append('missing_source_line')
    if not r.get('candidate_vulnerability') and 'vulnerability' not in r: warnings.append('missing_candidate_vulnerability')
    if not isinstance(r.get('evidence'), dict) or not r.get('evidence'): errors.append('missing_evidence_object')
    if status in CONFIRMED:
        for key in ['request_sample','response_sample','validation_run_id','role_context','scope_id']:
            if key not in ev and key not in r: errors.append('confirmed_missing_'+key)
        if 'quality_gate' not in r and 'quality_gate' not in ev: errors.append('confirmed_missing_quality_gate')
        if 'report_template' not in r and 'report_template' not in ev: errors.append('confirmed_missing_report_template')
        ok, reason = manifest_link_ok(r, manifest)
        if not ok: errors.append('confirmed_'+reason)
        elif reason == 'manifest_not_supplied': warnings.append('manifest_not_supplied_for_confirmed_record')
    elif status in CANDIDATE:
        if status == 'needs_review' and not (r.get('limitation') or r.get('review_reason')): warnings.append('needs_review_without_limitation')
        if status in {'blocked','conflict','rejected'} and not (r.get('limitation') or r.get('review_reason')): warnings.append(status+'_without_reason')
    else:
        warnings.append('unknown_review_status')
    return {'status':'fail' if errors else 'pass','errors':errors,'warnings':warnings}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input', action='append', required=True)
    ap.add_argument('--manifest', default=None, help='Optional evidence manifest for confirmed/reportable linkage checks')
    ap.add_argument('-o','--out',default='-')
    ap.add_argument('--fail-on-error', action='store_true')
    args=ap.parse_args()
    manifest=load_manifest(args.manifest) if args.manifest else None
    rows=[]; fail=0
    for p in args.input:
        for line_no,r in read_jsonl(p):
            sc=score_record(r, manifest); fail += 1 if sc['status']=='fail' else 0
            rows.append({'input':p,'line':line_no,'status':sc['status'],'errors':sc['errors'],'warnings':sc['warnings'],'candidate_vulnerability':r.get('candidate_vulnerability'),'review_status':r.get('review_status')})
    summary={'schema_version':'qg-jsonl-score.v2','inputs':args.input,'manifest':args.manifest,'total':len(rows),'failed':fail,'passed':len(rows)-fail,'records':rows}
    data=json.dumps(summary,ensure_ascii=False,indent=2)
    if args.out=='-': print(data)
    else: Path(args.out).write_text(data,encoding='utf-8')
    if args.fail_on_error and fail: sys.exit(4)
if __name__=='__main__': main()
