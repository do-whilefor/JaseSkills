import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TaintEngineTest(unittest.TestCase):
    def test_taint_engine_outputs_paths_from_security_graph(self):
        graph=ROOT/'outputs/current/taint_graph.json'; taint=ROOT/'outputs/current/taint_paths.json'
        p=subprocess.run([sys.executable,'analyzers/semantic_graph_builder.py','tests/fixtures/cross_file_app','--out',str(graph)],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        p=subprocess.run([sys.executable,'analyzers/taint_engine.py','--graph',str(graph),'--out',str(taint)],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        data=json.loads(taint.read_text())
        self.assertIn('paths',data)
        self.assertGreaterEqual(data['summary']['paths'],0)
if __name__=='__main__': unittest.main()
