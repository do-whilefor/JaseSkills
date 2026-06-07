import json, tempfile, unittest, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from quality.quality_gate import evaluate
ROOT=Path(__file__).resolve().parents[2]
class RedactionRequiredTest(unittest.TestCase):
    def test_unredacted_secret_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[{'finding_id':'s1','detector_id':'secret_leak','title':'secret','severity_candidate':'high','confidence':'high','affected_files':[{'path':'x.env','line':1}],'affected_routes':[],'source':'test','sink':'secret','dataflow_path':[],'auth_context':{},'tenant_context':{},'required_role':'unknown','evidence_refs':['ev1'],'replay_plan_id':'rp1','negative_test_id':'neg1','blocked_test_id':'blk1','review_status':'confirmed'}]}
            ev={'schema_version':'evidence-manifest-v1','policy':{},'evidence':[{'evidence_id':'ev1','type':'source_line','source_tool':'test','timestamp':'now','scope_status':'allowed','redaction_status':'failed_unredacted_secret','raw_path':'raw','sanitized_path':'san','related_finding':'s1','request_ref':'req','response_ref':'res','screenshot_ref':'shot','trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}]}
            rp={'results':[{'finding_id':'s1','status':'passed','request_ref':'req','response_ref':'res','screenshot_ref':'shot'}]}
            cf=td/'c.json'; ef=td/'e.json'; rf=td/'r.json'; cf.write_text(json.dumps(cand)); ef.write_text(json.dumps(ev)); rf.write_text(json.dumps(rp))
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertIn('unredacted_secret_blocks_report', q['findings'][0]['hard_failures'])
if __name__=='__main__': unittest.main()
