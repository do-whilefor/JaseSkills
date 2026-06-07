import unittest, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.tool_orchestrator import ToolOrchestrator
class ToolOrchestratorTest(unittest.TestCase):
    def test_unavailable_not_success(self):
        orch=ToolOrchestrator(Path(__file__).resolve().parents[1])
        result=orch.run('definitely-not-registered')
        self.assertEqual(result['status'], 'unavailable')
        self.assertFalse(result['available'])
    def test_python_version_succeeds_or_fails_truthfully(self):
        orch=ToolOrchestrator(Path(__file__).resolve().parents[1])
        result=orch.run('python-version')
        self.assertIn(result['status'], {'succeeded','failed','unavailable','blocked'})
        self.assertNotEqual(result['status'], 'unknown')
if __name__ == '__main__': unittest.main()
