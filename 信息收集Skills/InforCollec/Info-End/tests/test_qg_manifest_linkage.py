import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_qg_manifest_linkage_required_for_confirmed(tmp_path):
    manifest=tmp_path/'manifest.json'
    finding=tmp_path/'finding.jsonl'
    out=tmp_path/'score.json'
    manifest.write_text(json.dumps({'schema_version':'1.0','items':[{'evidence_id':'EV-good','kind':'request_summary','path':'evidence/request.json'}]}))
    good={'candidate_id':'F1','candidate_vulnerability':'idor','review_status':'confirmed','source_file':'app.py','source_line':1,'evidence':{'evidence_id':'EV-good','request_sample':{},'response_sample':{},'validation_run_id':'run1','role_context':'user','scope_id':'local','quality_gate':{}},'report_template':'templates/finding-detail.md'}
    bad={**good,'candidate_id':'F2','evidence':{**good['evidence'],'evidence_id':'EV-missing'}}
    finding.write_text(json.dumps(good)+'\n'+json.dumps(bad)+'\n')
    subprocess.run(['python3',str(ROOT/'scripts/qg-jsonl-score.py'),'--input',str(finding),'--manifest',str(manifest),'-o',str(out)],check=True)
    s=json.loads(out.read_text())
    assert s['total']==2 and s['failed']==1
    assert any('confirmed_missing_manifest_linkage' in r['errors'] for r in s['records'])
