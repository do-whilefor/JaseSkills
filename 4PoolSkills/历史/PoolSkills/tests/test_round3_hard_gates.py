import json, subprocess, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evidence.ref_validator import validate_evidence_manifest_refs
from quality.quality_gate import evaluate
from report.report_generator import generate
ROOT = Path(__file__).resolve().parents[1]


def base_finding(status='candidate', source='source_scan', dataflow=None, detector='rce'):
    return {
        'finding_id':'f-round3','detector_id':detector,'title':'round3','severity_candidate':'critical','confidence':'high',
        'affected_files':[{'path':'app.py','line':1}],'affected_routes':[],'source':source,'sink':'eval',
        'dataflow_path':dataflow or [{'kind':'file','path':'app.py','line':1},{'kind':'sink','name':'eval'}],
        'auth_context':{},'tenant_context':{},'required_role':'unknown','evidence_refs':['ev-round3'],
        'replay_plan_id':'rp-round3','negative_test_id':'neg-round3','blocked_test_id':'blk-round3','review_status':status,
    }


def manifest(td: Path, with_dynamic=False):
    san = td/'evidence/sanitized/ev-round3.txt'
    raw = td/'evidence/raw/ev-round3.txt'
    san.parent.mkdir(parents=True, exist_ok=True); raw.parent.mkdir(parents=True, exist_ok=True)
    san.write_text('safe sanitized evidence', encoding='utf-8'); raw.write_text('raw evidence', encoding='utf-8')
    item = {'evidence_id':'ev-round3','type':'source_line','source_tool':'test','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'evidence/raw/ev-round3.txt','sanitized_path':'evidence/sanitized/ev-round3.txt','related_finding':'f-round3','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}
    if with_dynamic:
        for name, field in [('req.json','request_ref'),('resp.json','response_ref'),('shot.png','screenshot_ref'),('dom.html','dom_ref')]:
            p=td/'evidence/dynamic'/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('x', encoding='utf-8')
            item[field]=str(p.relative_to(td))
    return {'schema_version':'evidence-manifest-v1','root':str(td),'policy':{},'evidence':[item]}

class Round3HardGatesTest(unittest.TestCase):
    def test_evidence_rejects_sanitized_path_outside_manifest_root(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            outside=Path('/tmp/outside-round3-evidence.txt')
            outside.write_text('outside', encoding='utf-8')
            cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[base_finding()]}
            ev={'schema_version':'evidence-manifest-v1','root':str(td),'policy':{},'evidence':[{'evidence_id':'ev-round3','type':'source_line','source_tool':'test','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'evidence/raw/x.txt','sanitized_path':str(outside),'related_finding':'f-round3','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}]}
            r=validate_evidence_manifest_refs(ev,cand)
            self.assertFalse(r['ok'])
            self.assertIn('sanitized_path_outside_manifest_root', {e['code'] for e in r['errors']})

    def test_severe_confirmed_requires_cross_file_source_sink_dataflow(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[base_finding(status='confirmed', source='source_scan')]}
            ev=manifest(td, with_dynamic=True)
            replay={'schema_version':'replay-result-v2','playwright_available':True,'role_tenant_matrix':{},'policy':'test','results':[{'finding_id':'f-round3','replay_plan_id':'rp-round3','status':'passed','role':None,'tenant':None,'request_ref':'evidence/dynamic/req.json','response_ref':'evidence/dynamic/resp.json','screenshot_ref':'evidence/dynamic/shot.png','trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':'evidence/dynamic/dom.html','matrix_results':[],'errors':[]}], 'blocked_controls':[]}
            cf=td/'c.json'; ef=td/'e.json'; rf=td/'r.json'
            cf.write_text(json.dumps(cand)); ef.write_text(json.dumps(ev)); rf.write_text(json.dumps(replay))
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertEqual(q['overall_status'], 'fail')
            self.assertEqual(q['findings'][0]['allowed_status'], 'candidate')
            self.assertIn('severe_confirmed_requires_cross_file_source_sink_dataflow', q['findings'][0]['hard_failures'])

    def test_quality_validates_replay_schema(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[base_finding()]}
            ev=manifest(td)
            bad_replay={'schema_version':'wrong','results':[]}
            cf=td/'c.json'; ef=td/'e.json'; rf=td/'bad_replay.json'
            cf.write_text(json.dumps(cand)); ef.write_text(json.dumps(ev)); rf.write_text(json.dumps(bad_replay))
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertEqual(q['overall_status'], 'fail')
            self.assertTrue(any(x.startswith('replay_schema_invalid:') for x in q['hard_failures']))

    def test_report_blocks_failed_quality_even_if_files_exist(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            cand={'schema_version':'finding-candidates-v1','scope':{},'findings':[base_finding()]}
            ev=manifest(td)
            q={'schema_version':'quality-result-v2','overall_status':'fail','hard_failures':['forced_fail'],'findings':[{'finding_id':'f-round3','allowed_status':'candidate','checks':{},'hard_failures':[]}]}
            cf=td/'c.json'; ef=td/'e.json'; qf=td/'q.json'; out=td/'report.md'
            cf.write_text(json.dumps(cand)); ef.write_text(json.dumps(ev)); qf.write_text(json.dumps(q))
            with self.assertRaises(RuntimeError) as ctx:
                generate(cf,ef,qf,out)
            self.assertIn('quality_gate_not_passed_report_blocked', str(ctx.exception))

    def test_tool_cli_unavailable_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'tool.json'
            p=subprocess.run([sys.executable, str(ROOT/'tools/tool_orchestrator.py'), '--root', str(ROOT), '--tool', 'definitely-not-registered', '--out', str(out)], text=True, capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            data=json.loads(out.read_text())
            self.assertEqual(data['status'], 'unavailable')
            self.assertFalse(data['result_is_success'])

if __name__ == '__main__':
    unittest.main()
