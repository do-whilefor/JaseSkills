import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from evidence.ref_validator import validate_evidence_manifest_refs
from quality.quality_gate import evaluate
from report.report_generator import generate
from analyzers.lang.rust_ast import parse_functions as parse_rust
from analyzers.lang.js_ts_ast import parse_functions as parse_js


def make_finding(status='confirmed', detector='rce', severity='critical', source='cross_file_dataflow', evidence_refs=None, auth=None, tenant=None, replay_plan_id='rp1', negative='neg1', blocked='blk1'):
    return {
        'finding_id':'f1','detector_id':detector,'title':'x','severity_candidate':severity,'confidence':'high',
        'affected_files':[{'path':'app.py','line':1}], 'affected_routes':[], 'source':source, 'sink':'eval_vm',
        'dataflow_path':[{'kind':'route','file':'app.py','line':1},{'kind':'function','file':'app.py','line':2},{'kind':'sink','file':'app.py','line':3}],
        'auth_context': auth or {'required':'unknown'}, 'tenant_context': tenant or {'required':'unknown'}, 'required_role':'unknown',
        'evidence_refs': evidence_refs if evidence_refs is not None else ['ev1'], 'replay_plan_id': replay_plan_id,
        'negative_test_id': negative, 'blocked_test_id': blocked, 'review_status':status
    }


def write_manifest(td: Path, dynamic=True, source_tool='test', redaction='clean', secret_text=None):
    san = td/'evidence/sanitized/ev1.txt'; raw = td/'evidence/raw/ev1.txt'
    san.parent.mkdir(parents=True, exist_ok=True); raw.parent.mkdir(parents=True, exist_ok=True)
    san.write_text(secret_text or 'sanitized evidence', encoding='utf-8'); raw.write_text('raw evidence', encoding='utf-8')
    item = {'evidence_id':'ev1','type':'source_line','source_tool':source_tool,'timestamp':'now','scope_status':'allowed','redaction_status':redaction,'raw_path':'evidence/raw/ev1.txt','sanitized_path':'evidence/sanitized/ev1.txt','related_finding':'f1','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None}
    if dynamic:
        for name, field in [('req.json','request_ref'),('resp.json','response_ref'),('shot.png','screenshot_ref'),('trace.zip','trace_ref'),('capture.har','har_ref'),('console.json','console_ref'),('dom.html','dom_ref')]:
            p = td/'evidence/dynamic'/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('x', encoding='utf-8')
            item[field]=f'evidence/dynamic/{name}'
    return {'schema_version':'evidence-manifest-v1','root':str(td),'policy':{},'evidence':[item]}


def write_replay(manifest_backed=True, status='passed', role='user', tenant='tenant-a', neg='passed', blk='passed'):
    def ref(x): return f'evidence/dynamic/{x}' if manifest_backed else f'evidence/fake/{x}'
    return {'schema_version':'replay-result-v2','playwright_available':True,'role_tenant_matrix':{'roles':['user'],'tenants':['tenant-a']},'policy':'test','blocked_controls':[], 'results':[{'finding_id':'f1','replay_plan_id':'rp1','status':status,'role':role,'tenant':tenant,'request_ref':ref('req.json'),'response_ref':ref('resp.json'),'screenshot_ref':ref('shot.png'),'trace_ref':ref('trace.zip'),'har_ref':ref('capture.har'),'console_ref':ref('console.json'),'dom_ref':ref('dom.html'),'matrix_results':[],'errors':[],'negative_status':neg,'blocked_status':blk}]}


def write_jsons(td: Path, finding, ev, rp=None):
    cf, ef, rf = td/'c.json', td/'e.json', td/'r.json'
    cf.write_text(json.dumps({'schema_version':'finding-candidates-v1','scope':{},'findings':[finding]}), encoding='utf-8')
    ef.write_text(json.dumps(ev), encoding='utf-8')
    if rp is not None:
        rf.write_text(json.dumps(rp), encoding='utf-8')
        return cf, ef, rf
    return cf, ef, None


class UltimateAntiFraudTest(unittest.TestCase):
    def test_tool_unavailable_cli_is_nonzero(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)/'tool.json'
            p = subprocess.run([sys.executable, str(ROOT/'tools/tool_orchestrator.py'), '--root', str(ROOT), '--tool', 'not-a-real-tool', '--out', str(out)], text=True, capture_output=True)
            self.assertNotEqual(p.returncode, 0)
            self.assertFalse(json.loads(out.read_text())['result_is_success'])

    def test_confirmed_requires_manifest_backed_dynamic_refs(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); f=make_finding(); ev=write_manifest(td, dynamic=True); rp=write_replay(manifest_backed=False)
            cf,ef,rf=write_jsons(td,f,ev,rp)
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertEqual(q['findings'][0]['allowed_status'],'candidate')
            self.assertIn('replay_request_ref_not_in_evidence_manifest', q['findings'][0]['hard_failures'])

    def test_negative_test_missing_blocks_confirmed(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); cf,ef,rf=write_jsons(td,make_finding(),write_manifest(td),write_replay(neg='not_executed'))
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertIn('missing_or_failed_negative_test', q['findings'][0]['hard_failures'])

    def test_blocked_control_missing_blocks_confirmed(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); cf,ef,rf=write_jsons(td,make_finding(),write_manifest(td),write_replay(blk='not_executed'))
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertIn('missing_or_failed_blocked_test_control', q['findings'][0]['hard_failures'])

    def test_role_matrix_placeholder_blocks_authz_confirmed(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); f=make_finding(detector='authz_bypass', auth={'role':'matrix_required'}, tenant={'tenant':'tenant-a'})
            cf,ef,rf=write_jsons(td,f,write_manifest(td),write_replay(role=None, tenant='tenant-a'))
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertIn('role_tenant_matrix_missing_or_placeholder', q['findings'][0]['hard_failures'])

    def test_tenant_matrix_placeholder_blocks_tenant_confirmed(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); f=make_finding(detector='tenant_isolation', auth={'role':'user'}, tenant={'tenant':'matrix_required'})
            cf,ef,rf=write_jsons(td,f,write_manifest(td),write_replay(role='user', tenant=None))
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertIn('role_tenant_matrix_missing_or_placeholder', q['findings'][0]['hard_failures'])

    def test_missing_evidence_ref_blocks_report(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); f=make_finding(evidence_refs=['missing']); ev=write_manifest(td); rp=write_replay()
            cf,ef,rf=write_jsons(td,f,ev,rp)
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertEqual(q['overall_status'],'fail')
            self.assertIn('evidence_ref_integrity_failed', q['hard_failures'])

    def test_secret_content_in_sanitized_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); ev=write_manifest(td, secret_text='api_key="1234567890abcdef"')
            r=validate_evidence_manifest_refs(ev, {'findings':[make_finding()]})
            self.assertFalse(r['ok'])
            self.assertIn('sanitized_path_contains_unredacted_secret', {e['code'] for e in r['errors']})

    def test_scope_outside_collector_fails(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'root'; root.mkdir(); (root/'scope.yaml').write_text('allowed_roots: [.]\ndenied_roots: []\n', encoding='utf-8')
            out=Path(td)/'out.json'; outside=Path(td)/'outside'; outside.mkdir(); (outside/'app.py').write_text('@app.get("/x")\ndef x(): pass')
            p=subprocess.run([sys.executable, str(ROOT/'collectors/route_collector.py'), str(outside), '--scope-file', str(root/'scope.yaml'), '--out', str(out)], text=True, capture_output=True)
            self.assertNotEqual(p.returncode, 0)

    def test_symlink_sanitized_evidence_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); ev=write_manifest(td); target=td/'target.txt'; target.write_text('x'); san=td/'evidence/sanitized/ev1.txt'; san.unlink(); os.symlink(target, san)
            r=validate_evidence_manifest_refs(ev, {'findings':[make_finding()]})
            self.assertFalse(r['ok'])
            self.assertIn('sanitized_path_symlink_forbidden', {e['code'] for e in r['errors']})

    def test_parser_failure_is_not_ast_success(self):
        result=parse_rust('fn main( {')
        self.assertIn(result['status'], {'parser_error','parser_unavailable'})
        self.assertNotEqual(result['status'], 'parsed')

    def test_js_parser_uses_typescript_or_declares_unavailable(self):
        result=parse_js('export function a(){ fetch("/api/x") }')
        self.assertIn(result['status'], {'parsed','parser_error','parser_unavailable'})
        self.assertNotEqual(result.get('parser'), 'js_ts_ast.regex_fallback_not_ast')

    def test_replay_failed_downgrades_confirmed(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); cf,ef,rf=write_jsons(td,make_finding(),write_manifest(td),write_replay(status='not_reproducible'))
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertIn('replay_failed_missing_or_not_manifest_backed', q['findings'][0]['hard_failures'])

    def test_ai_text_as_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); cf,ef,rf=write_jsons(td,make_finding(),write_manifest(td, source_tool='ai'),write_replay())
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertIn('ai_text_not_evidence:ev1', q['findings'][0]['hard_failures'])

    def test_empty_detector_rule_rejected_by_selftest(self):
        with tempfile.TemporaryDirectory() as td:
            bad=Path(td)/'rules.yaml'; bad.write_text('rules:\n- id: empty\n  title: empty\n', encoding='utf-8')
            p=subprocess.run([sys.executable, str(ROOT/'scripts/detector_registry_selftest.py'), '--rules', str(bad)], text=True, capture_output=True)
            self.assertNotEqual(p.returncode, 0)

    def test_schema_mismatch_quality_fails(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); (td/'c.json').write_text(json.dumps({'schema_version':'bad','findings':[]}), encoding='utf-8')
            ev=write_manifest(td); (td/'e.json').write_text(json.dumps(ev), encoding='utf-8')
            q=evaluate(td/'c.json', td/'e.json', None, ROOT/'scope.yaml')
            self.assertTrue(any(x.startswith('detector_schema_invalid:') for x in q['hard_failures']))

    def test_confirmed_requires_request_response_visual(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); cf,ef,rf=write_jsons(td,make_finding(),write_manifest(td, dynamic=False),write_replay())
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertIn('missing_manifest_backed_dynamic_request', q['findings'][0]['hard_failures'])
            self.assertIn('missing_manifest_backed_dynamic_response', q['findings'][0]['hard_failures'])
            self.assertIn('missing_manifest_backed_screenshot_or_dom', q['findings'][0]['hard_failures'])

    def test_severe_missing_replay_plan_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); f=make_finding(replay_plan_id=''); cf,ef,rf=write_jsons(td,f,write_manifest(td),write_replay())
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertIn('severe_finding_missing_replay_plan_id', q['findings'][0]['hard_failures'])

    def test_authz_finding_requires_role_and_tenant_context(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); f=make_finding(detector='idor_bola', auth={'role':'user'}, tenant={'tenant':'tenant-a'})
            cf,ef,rf=write_jsons(td,f,write_manifest(td),write_replay(role='user', tenant='tenant-a'))
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml')
            self.assertTrue(q['findings'][0]['checks']['role_tenant'])

    def test_report_does_not_reference_raw_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); f=make_finding(status='candidate'); cf,ef,rf=write_jsons(td,f,write_manifest(td),write_replay())
            q=evaluate(cf,ef,rf,ROOT/'scope.yaml'); qf=td/'q.json'; qf.write_text(json.dumps(q), encoding='utf-8')
            out=td/'report.md'; generate(cf,ef,qf,out)
            text=out.read_text()
            self.assertNotIn('evidence/raw', text)

    def test_failed_command_preserves_stderr_exit_code(self):
        with tempfile.TemporaryDirectory() as td:
            reg=Path(td)/'tools.yaml'; reg.write_text('tools:\n  failer:\n    executable: python3\n    default_args: [-c, "import sys; print(\'ERR\', file=sys.stderr); sys.exit(7)"]\n    requires_network: false\n', encoding='utf-8')
            out=Path(td)/'tool.json'
            p=subprocess.run([sys.executable, str(ROOT/'tools/tool_orchestrator.py'), '--root', str(ROOT), '--registry', str(reg), '--tool', 'failer', '--out', str(out)], text=True, capture_output=True)
            data=json.loads(out.read_text())
            self.assertEqual(data['status'], 'failed')
            self.assertEqual(data['exit_code'], 7)
            self.assertIn('ERR', data['stderr_summary'])
            self.assertNotEqual(p.returncode, 0)

if __name__ == '__main__':
    unittest.main()
