import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class EvidenceRedactionTest(unittest.TestCase):
    def test_evidence_schema_and_sanitized_only(self):
        cand=ROOT/'outputs/current/test_findings_for_evidence.json'
        subprocess.run([sys.executable,'detectors/detector_runner.py','tests/fixtures/engine_project','--out',str(cand)],cwd=ROOT,check=True)
        out=ROOT/'outputs/current/evidence_manifest_test.json'
        p=subprocess.run([sys.executable,'evidence/evidence_manifest_builder.py','--root','tests/fixtures/engine_project','--candidates',str(cand),'--out',str(out)],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr)
        data=json.loads(out.read_text())
        self.assertTrue(data['policy']['raw_and_sanitized_separated'])
        self.assertTrue(all('sanitized_path' in e for e in data['evidence']))
if __name__ == '__main__': unittest.main()
