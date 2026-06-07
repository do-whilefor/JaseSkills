import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DetectorEngineTest(unittest.TestCase):
    def test_detector_outputs_candidates(self):
        out=ROOT/'outputs/current/test_findings.json'; out.parent.mkdir(parents=True,exist_ok=True)
        p=subprocess.run([sys.executable,'detectors/detector_runner.py','tests/fixtures/engine_project','--out',str(out)],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        data=json.loads(out.read_text())
        self.assertGreater(len(data['findings']),0)
        self.assertTrue(all(f['review_status']=='candidate' for f in data['findings']))
if __name__ == '__main__': unittest.main()
