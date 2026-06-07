import json, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import load_scope, path_decision
from evidence.evidence_manifest_builder import build
from quality.quality_gate import evaluate

class WindowsScopeAndQualityRootTest(unittest.TestCase):
    def test_external_target_without_scope_gets_target_local_default(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / 'external repo with spaces'
            root.mkdir()
            src = root / 'app.py'
            src.write_text('print("ok")\n', encoding='utf-8')
            scope = load_scope(root)
            self.assertTrue(scope.get('_generated_default_scope'))
            self.assertTrue(path_decision(src, root, scope).allowed)

    def test_evidence_id_cannot_escape_evidence_directory(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'scope.yaml').write_text("""allowed_roots: [.]
denied_roots: []
""", encoding='utf-8')
            (root / 'app.py').write_text('secret = "safe"\n', encoding='utf-8')
            cand = {
                'schema_version': 'finding-candidates-v1',
                'scope': {},
                'findings': [{
                    'finding_id': 'finding-1', 'detector_id': 'idor_bola', 'title': 'x',
                    'severity_candidate': 'medium', 'confidence': 'medium',
                    'affected_files': [{'path': 'app.py', 'line': 1}], 'affected_routes': [],
                    'source': 'source_scan', 'sink': 'x', 'dataflow_path': [{'kind': 'file'}, {'kind': 'sink'}],
                    'auth_context': {'required': 'unknown'}, 'tenant_context': {'required': 'unknown'},
                    'evidence_refs': ['../outside:bad'], 'review_status': 'candidate',
                    'evidence_inline': [{'evidence_id': '../outside:bad', 'type': 'source_line', 'source_file': 'app.py', 'line': 1, 'summary': 'x'}]
                }]
            }
            cf = root / 'candidates.json'; cf.write_text(json.dumps(cand), encoding='utf-8')
            manifest = build(root, cf)
            san = manifest['evidence'][0]['sanitized_path']
            self.assertFalse('..' in Path(san).parts)
            self.assertTrue((root / san).resolve().is_file())
            self.assertTrue(str((root / san).resolve()).startswith(str((root / 'evidence' / 'sanitized').resolve())))


    def test_evidence_filename_handles_windows_reserved_names_and_collisions(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / 'scope.yaml').write_text("""allowed_roots: [.]
denied_roots: []
""", encoding='utf-8')
            (root / 'app.py').write_text('print("ok")\n', encoding='utf-8')
            cand = {
                'schema_version': 'finding-candidates-v1',
                'scope': {},
                'findings': [{
                    'finding_id': 'finding-1', 'detector_id': 'idor_bola', 'title': 'x',
                    'severity_candidate': 'medium', 'confidence': 'medium',
                    'affected_files': [{'path': 'app.py', 'line': 1}], 'affected_routes': [],
                    'source': 'source_scan', 'sink': 'x', 'dataflow_path': [{'kind': 'file'}, {'kind': 'sink'}],
                    'auth_context': {'required': 'unknown'}, 'tenant_context': {'required': 'unknown'},
                    'evidence_refs': ['CON.txt', 'a/b', 'a:b'], 'review_status': 'candidate',
                    'evidence_inline': [
                        {'evidence_id': 'CON.txt', 'type': 'source_line', 'source_file': 'app.py', 'line': 1, 'summary': 'x'},
                        {'evidence_id': 'a/b', 'type': 'source_line', 'source_file': 'app.py', 'line': 1, 'summary': 'x'},
                        {'evidence_id': 'a:b', 'type': 'source_line', 'source_file': 'app.py', 'line': 1, 'summary': 'x'}
                    ]
                }]
            }
            cf = root / 'candidates.json'; cf.write_text(json.dumps(cand), encoding='utf-8')
            manifest = build(root, cf)
            names = [Path(e['sanitized_path']).name for e in manifest['evidence']]
            self.assertEqual(len(names), len(set(names)))
            self.assertTrue(all((root / e['sanitized_path']).is_file() for e in manifest['evidence']))
            self.assertFalse(any(name.upper().startswith('CON.') for name in names))

    def test_quality_uses_manifest_root_for_dynamic_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            target = base / 'target'; target.mkdir()
            outdir = base / 'outputs'; outdir.mkdir()
            (target / 'scope.yaml').write_text("""allowed_roots: [.]
denied_roots: []
network_policy:
  allowed_hosts: [127.0.0.1, localhost]
""", encoding='utf-8')
            for rel in ['evidence/sanitized/ev-static.txt','evidence/raw/ev-static.txt','req.json','resp.json','dom.html']:
                p = target / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('ok', encoding='utf-8')
            cand = {'schema_version':'finding-candidates-v1','scope':{},'findings':[{
                'finding_id':'finding-1','detector_id':'idor_bola','title':'x','severity_candidate':'high','confidence':'high',
                'affected_files':[{'path':'a.py','line':1}], 'affected_routes':[], 'source':'cross_file_dataflow','sink':'sql_or_nosql_query',
                'dataflow_path':[{'kind':'route'},{'kind':'function'},{'kind':'sink'}], 'auth_context':{'role':'user'}, 'tenant_context':{'tenant':'tenant_a'},
                'required_role':'user','evidence_refs':['ev-static'],'replay_plan_id':'rp-1','negative_test_id':'neg-1','blocked_test_id':'blk-1','review_status':'confirmed'}]}
            manifest = {'schema_version':'evidence-manifest-v1','root':str(target),'policy':{},'evidence':[
                {'evidence_id':'ev-static','type':'source_line','source_tool':'test','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'evidence/raw/ev-static.txt','sanitized_path':'evidence/sanitized/ev-static.txt','related_finding':'finding-1','source_file':'a.py','related_route':None,'related_role':None,'related_tenant':None,'request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None},
                {'evidence_id':'ev-dyn','type':'dynamic_replay','source_tool':'playwright_runner','timestamp':'now','scope_status':'allowed','redaction_status':'clean','raw_path':'evidence/raw/ev-static.txt','sanitized_path':'evidence/sanitized/ev-static.txt','related_finding':'finding-1','source_file':None,'related_route':None,'related_role':'user','related_tenant':'tenant_a','replay_plan_id':'rp-1','request_ref':'req.json','response_ref':'resp.json','screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':'dom.html'}
            ]}
            replay = {'schema_version':'replay-result-v2','playwright_available':True,'role_tenant_matrix':{},'policy':'p','results':[{'finding_id':'finding-1','replay_plan_id':'rp-1','status':'passed','role':'user','tenant':'tenant_a','request_ref':'req.json','response_ref':'resp.json','screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':'dom.html','matrix_results':[],'errors':[],'negative_status':'passed','blocked_status':'passed'}]}
            cf=outdir/'c.json'; ef=outdir/'e.json'; rf=outdir/'r.json'
            cf.write_text(json.dumps(cand), encoding='utf-8'); ef.write_text(json.dumps(manifest), encoding='utf-8'); rf.write_text(json.dumps(replay), encoding='utf-8')
            q = evaluate(cf, ef, rf, target/'scope.yaml')
            self.assertEqual(q['findings'][0]['allowed_status'], 'confirmed', q)
            self.assertTrue(q['findings'][0]['checks']['manifest_backed_request'])

if __name__ == '__main__':
    unittest.main()
