import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class BusinessLogicOracleTest(unittest.TestCase):
    def test_property_oracle_pass_and_fail(self):
        out=ROOT/'outputs/current/business_oracle_pass.json'
        p=subprocess.run([sys.executable,'business_logic/property_oracle.py','--spec','tests/fixtures/business_oracle/invariants.json','--events','tests/fixtures/business_oracle/events_pass.json','--out',str(out)],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        self.assertEqual(json.loads(out.read_text())['status'],'passed')
        out2=ROOT/'outputs/current/business_oracle_fail.json'
        p=subprocess.run([sys.executable,'business_logic/property_oracle.py','--spec','tests/fixtures/business_oracle/invariants.json','--events','tests/fixtures/business_oracle/events_fail.json','--out',str(out2)],cwd=ROOT,text=True,capture_output=True)
        self.assertNotEqual(p.returncode,0)
        self.assertEqual(json.loads(out2.read_text())['status'],'failed')
    def test_state_machine_replay(self):
        out=ROOT/'outputs/current/state_machine_pass.json'
        p=subprocess.run([sys.executable,'business_logic/state_machine_replay.py','--machine','tests/fixtures/business_oracle/machine.json','--events','tests/fixtures/business_oracle/events_pass.json','--out',str(out)],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)

if __name__=='__main__': unittest.main()
