import json, tempfile, unittest, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from dynamic.evidence_collector import stitch_dynamic
from quality.quality_gate import evaluate

class DynamicEvidenceStitchingTest(unittest.TestCase):
    def test_stitched_dynamic_refs_can_support_confirmed_only_when_manifest_backed(self):
        with tempfile.TemporaryDirectory() as td:
            r=Path(td)
            (r/'scope.yaml').write_text('allowed_roots:\n  - .\ndenied_roots: []\nnetwork_policy:\n  allowed_hosts: [127.0.0.1, localhost]\n',encoding='utf-8')
            (r/'evidence/sanitized').mkdir(parents=True)
            (r/'evidence/raw').mkdir(parents=True)
            (r/'evidence/sanitized/ev-static.txt').write_text('safe source evidence',encoding='utf-8')
            (r/'evidence/raw/ev-static.txt').write_text('safe source evidence',encoding='utf-8')
            for name in ['req.json','resp.json','shot.png','dom.html']:
                (r/name).write_text('artifact',encoding='utf-8')
            cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[{
                'finding_id':'finding-1','detector_id':'idor_bola','title':'x','severity_candidate':'high','confidence':'high','affected_files':[{'path':'a.py','line':1}], 'affected_routes':[], 'source':'cross_file_dataflow','sink':'sql_or_nosql_query','dataflow_path':[{'kind':'route'},{'kind':'function'},{'kind':'sink'}], 'auth_context':{'role':'user'}, 'tenant_context':{'tenant':'tenant_a'}, 'required_role':'user','evidence_refs':['ev-static'],'replay_plan_id':'rp-1','negative_test_id':'neg-1','blocked_test_id':'blk-1','review_status':'confirmed'}]}
            manifest={'schema_version':'evidence-manifest-v1','policy':{},'evidence':[{'evidence_id':'ev-static','type':'source_line','source_tool':'test','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'evidence/raw/ev-static.txt','sanitized_path':'evidence/sanitized/ev-static.txt','related_finding':'finding-1','source_file':'a.py','related_route':None,'related_role':None,'related_tenant':None,'request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}]}
            replay={'schema_version':'replay-result-v2','playwright_available':True,'role_tenant_matrix':{},'policy':'p','results':[{'finding_id':'finding-1','replay_plan_id':'rp-1','status':'passed','role':'user','tenant':'tenant_a','request_ref':'req.json','response_ref':'resp.json','screenshot_ref':'shot.png','trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':'dom.html','matrix_results':[],'errors':[],'negative_status':'passed','blocked_status':'passed'}]}
            (r/'candidates.json').write_text(json.dumps(cand),encoding='utf-8')
            (r/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
            (r/'replay.json').write_text(json.dumps(replay),encoding='utf-8')
            stitched=stitch_dynamic(r/'manifest.json', r/'replay.json', r)
            (r/'manifest.stitched.json').write_text(json.dumps(stitched),encoding='utf-8')
            q=evaluate(r/'candidates.json', r/'manifest.stitched.json', r/'replay.json', r/'scope.yaml')
            f=q['findings'][0]
            self.assertEqual(f['allowed_status'],'confirmed', f)
            self.assertTrue(f['checks']['manifest_backed_request'])
            self.assertTrue(any(e['type']=='dynamic_replay' for e in stitched['evidence']))

if __name__=='__main__': unittest.main()
