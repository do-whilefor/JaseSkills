import json, tempfile, unittest, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from quality.quality_gate import evaluate
ROOT=Path(__file__).resolve().parents[2]
BASE={'finding_id':'adv1','detector_id':'rce','title':'RCE','severity_candidate':'critical','confidence':'medium','affected_files':[{'path':'x.py','line':1}],'affected_routes':[],'source':'test','sink':'eval','dataflow_path':[],'auth_context':{},'tenant_context':{},'required_role':'unknown','evidence_refs':['ev1'],'replay_plan_id':'rp1','negative_test_id':'neg1','blocked_test_id':'blk1'}
class NoFakeConfirmedTest(unittest.TestCase):
    def test_ai_or_manual_claim_cannot_confirm(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); f=dict(BASE); f['review_status']='confirmed'; f['ai_claim']='verified by reasoning'
            cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[f]}
            ev={'schema_version':'evidence-manifest-v1','policy':{},'evidence':[{'evidence_id':'ev1','type':'source_line','source_tool':'ai','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'raw','sanitized_path':'san','related_finding':'adv1','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}]}
            cf=td/'c.json'; ef=td/'e.json'; cf.write_text(json.dumps(cand)); ef.write_text(json.dumps(ev))
            q=evaluate(cf,ef,None,ROOT/'scope.yaml')
            self.assertEqual(q['findings'][0]['allowed_status'],'candidate')
if __name__=='__main__': unittest.main()
