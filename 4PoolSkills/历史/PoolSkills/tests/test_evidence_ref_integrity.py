import json, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence.ref_validator import validate_evidence_manifest_refs
from report.report_generator import generate
ROOT=Path(__file__).resolve().parents[1]
class EvidenceRefIntegrityTest(unittest.TestCase):
    def test_validator_rejects_missing_sanitized_path_and_missing_finding_ref(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[{'finding_id':'f1','detector_id':'ssrf','title':'x','severity_candidate':'high','confidence':'medium','affected_files':[{'path':'a.py','line':1}],'affected_routes':[],'source':'test','sink':'x','dataflow_path':[],'auth_context':{},'tenant_context':{},'required_role':'unknown','evidence_refs':['ev-missing'],'replay_plan_id':'rp','negative_test_id':'neg','blocked_test_id':'blk','review_status':'candidate'}]}
            ev={'schema_version':'evidence-manifest-v1','root':str(td),'policy':{},'evidence':[{'evidence_id':'ev1','type':'source_line','source_tool':'test','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'evidence/raw/ev1.txt','sanitized_path':'evidence/sanitized/ev1.txt','related_finding':'f1','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}]}
            r=validate_evidence_manifest_refs(ev,cand)
            self.assertFalse(r['ok'])
            codes={e['code'] for e in r['errors']}
            self.assertIn('sanitized_path_not_readable', codes)
            self.assertIn('finding_evidence_ref_missing_from_manifest', codes)

    def test_report_generation_preflight_rejects_missing_sanitized_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[{'finding_id':'f1','detector_id':'ssrf','title':'x','severity_candidate':'high','confidence':'medium','affected_files':[{'path':'a.py','line':1}],'affected_routes':[],'source':'test','sink':'x','dataflow_path':[],'auth_context':{},'tenant_context':{},'required_role':'unknown','evidence_refs':['ev1'],'replay_plan_id':'rp','negative_test_id':'neg','blocked_test_id':'blk','review_status':'candidate'}]}
            ev={'schema_version':'evidence-manifest-v1','root':str(td),'policy':{},'evidence':[{'evidence_id':'ev1','type':'source_line','source_tool':'test','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'evidence/raw/ev1.txt','sanitized_path':'evidence/sanitized/ev1.txt','related_finding':'f1','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}]}
            q={'schema_version':'quality-result-v2','overall_status':'pass','findings':[{'finding_id':'f1','allowed_status':'candidate','checks':{},'hard_failures':[]}]}
            cf=td/'c.json'; ef=td/'e.json'; qf=td/'q.json'; out=td/'r.md'
            cf.write_text(json.dumps(cand)); ef.write_text(json.dumps(ev)); qf.write_text(json.dumps(q))
            with self.assertRaises(RuntimeError): generate(cf,ef,qf,out)
if __name__=='__main__': unittest.main()
