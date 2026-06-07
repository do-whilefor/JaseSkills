#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'schemas' / 'EVIDENCE_MANIFEST_SCHEMA.json'

def basic_validate(d):
    errors=[]
    if not isinstance(d,dict): return ['manifest_not_object']
    for k in ['manifest_version','generated_at','scope','candidates']:
        if k not in d: errors.append('missing:'+k)
    if d.get('manifest_version')!='4.0': errors.append('manifest_version_not_4.0')
    scope=d.get('scope') or {}
    if scope.get('mode')!='local_authorized': errors.append('scope_mode_not_local_authorized')
    if not isinstance(d.get('candidates'), list): errors.append('candidates_not_array')
    for i,c in enumerate(d.get('candidates') if isinstance(d.get('candidates'),list) else []):
        for k in ['id','type','severity','status','source','code_evidence','dynamic_evidence','negative_controls','state_history','impact_proof','false_positive_exclusions','quality_gate','report_mapping','non_destructive']:
            if k not in c: errors.append(f'candidate[{i}].missing:{k}')
        nd=c.get('non_destructive') or {}
        if nd.get('is_non_destructive') is not True or nd.get('data_modified') is not False:
            errors.append(f'candidate[{i}].destructive_or_modified')
    return errors

def schema_validate(data):
    try:
        import jsonschema
        schema=json.loads(SCHEMA.read_text(encoding='utf-8'))
        jsonschema.Draft202012Validator.check_schema(schema)
        errors=sorted(jsonschema.Draft202012Validator(schema).iter_errors(data), key=lambda e: list(e.path))
        return [f"json_schema:{'/'.join(map(str,e.path)) or '<root>'}:{e.message}" for e in errors]
    except ImportError:
        return basic_validate(data)
    except Exception as e:
        return ['schema_validator_error:'+str(e)]

def quality_validate(d):
    results=[]
    for c in d.get('candidates',[]) if isinstance(d,dict) else []:
        e=[]
        if c.get('status') in ['confirmed','promoted']:
            if not c.get('code_evidence'): e.append('missing_code_evidence')
            if not c.get('dynamic_evidence'): e.append('missing_dynamic_evidence')
            if not c.get('negative_controls'): e.append('missing_negative_controls')
            if not c.get('impact_proof'): e.append('missing_impact_proof')
            if not c.get('false_positive_exclusions'): e.append('missing_false_positive_exclusions')
            if (c.get('quality_gate') or {}).get('score',0) < 85: e.append('quality_score_lt_85')
        nd=c.get('non_destructive') or {}
        if nd.get('is_non_destructive') is not True or nd.get('data_modified') is not False: e.append('non_destructive_boundary_failed')
        results.append({'id':c.get('id'), 'valid':not e, 'errors':e})
    return results

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('manifest'); ap.add_argument('--out', default=str(ROOT/'outputs/evidence_validation.json')); a=ap.parse_args()
    data=json.loads(Path(a.manifest).read_text(encoding='utf-8'))
    schema_errors=schema_validate(data)
    candidate_results=quality_validate(data) if not schema_errors else []
    out={'schema_version':'evidence-validation-v4.1','status':'pass' if not schema_errors and all(x['valid'] for x in candidate_results) else 'fail','schema_errors':schema_errors,'candidate_results':candidate_results,'schema_path':str(SCHEMA)}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0 if out['status']=='pass' else 2
if __name__=='__main__':
    raise SystemExit(main())
