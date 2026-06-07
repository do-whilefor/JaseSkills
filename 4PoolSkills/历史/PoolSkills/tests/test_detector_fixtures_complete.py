import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DetectorFixtureCompletenessTest(unittest.TestCase):
    def test_every_detector_has_four_state_independent_fixture_app(self):
        idx=json.loads((ROOT/'tests/fixtures/vulnerable_apps/FIXTURE_INDEX.json').read_text())
        required=set(idx['required_states'])
        self.assertEqual(required, {'positive','negative','blocked','needs_review'})
        self.assertGreaterEqual(len(idx['detectors']), 40)
        for det in idx['detectors']:
            states={Path(p).parent.name for p in det['states']}
            self.assertEqual(states, required, det['detector_id'])
            for p in det['states']:
                case=ROOT/p
                self.assertTrue(case.exists(), p)
                self.assertTrue((case.parent/'app.js').exists(), p)
                data=json.loads(case.read_text())
                self.assertEqual(data['detector_id'], det['detector_id'])
                self.assertIn('confirmed_standard', data)
if __name__=='__main__': unittest.main()
