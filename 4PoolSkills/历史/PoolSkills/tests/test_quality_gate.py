import json, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from quality.quality_gate import evaluate
ROOT=Path(__file__).resolve().parents[1]
class QualityGateTest(unittest.TestCase):
    def test_confirmed_without_dynamic_is_downgraded(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[{'finding_id':'f1','detector_id':'idor_bola','title':'x','severity_candidate':'high','confidence':'high','affected_files':[{'path':'a.py','line':1}],'affected_routes':[],'source':'test','sink':'test','dataflow_path':[],'auth_context':{},'tenant_context':{},'required_role':'user','evidence_refs':['ev1'],'replay_plan_id':'rp1','negative_test_id':'neg1','blocked_test_id':'blk1','review_status':'confirmed'}]}
            ev={'schema_version':'evidence-manifest-v1','policy':{},'evidence':[{'evidence_id':'ev1','type':'source_line','source_tool':'test','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'evidence/raw/ev1.txt','sanitized_path':'evidence/sanitized/ev1.txt','related_finding':'f1','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}]}
            cf=td/'c.json'; ef=td/'e.json'; of=td/'q.json'
            cf.write_text(json.dumps(cand)); ef.write_text(json.dumps(ev))
            q=evaluate(cf,ef,None,ROOT/'scope.yaml')
            self.assertEqual(q['overall_status'],'fail')
            self.assertEqual(q['findings'][0]['allowed_status'],'candidate')
            self.assertIn('missing_dynamic_request', q['findings'][0]['hard_failures'])
if __name__ == '__main__': unittest.main()
