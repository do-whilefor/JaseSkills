import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class CrossFileDataflowTest(unittest.TestCase):
    def test_security_graph_has_cross_file_call_to_sink_and_detector_uses_it(self):
        graph=ROOT/'outputs/current/cross_file_graph.json'; findings=ROOT/'outputs/current/cross_file_findings.json'
        p=subprocess.run([sys.executable,'analyzers/semantic_graph_builder.py','tests/fixtures/cross_file_app','--out',str(graph)],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        g=json.loads(graph.read_text())
        self.assertTrue(any(e['type']=='CALL_TO_FUNCTION' and e.get('data',{}).get('cross_file') for e in g['edges']))
        p=subprocess.run([sys.executable,'detectors/detector_runner.py','tests/fixtures/cross_file_app','--graph',str(graph),'--out',str(findings)],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        data=json.loads(findings.read_text())
        self.assertTrue(any(f['source']=='cross_file_dataflow' for f in data['findings']))
if __name__=='__main__': unittest.main()
