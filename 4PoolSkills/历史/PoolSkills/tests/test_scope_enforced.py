import os, tempfile, unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import load_scope, path_decision, redact_text, payload_decision
class ScopeTest(unittest.TestCase):
    def test_symlink_and_secret_and_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'scope.yaml').write_text("""allowed_roots: [.]
denied_roots: []
excluded_extensions: [.db]
max_file_size: 10000
symlink_policy: no_follow
destructive_action_blocklist: ["DROP TABLE"]
""", encoding='utf-8')
            outside=Path(td).parent/'outside_secret.txt'; outside.write_text('x')
            os.symlink(outside, root/'link.txt')
            scope=load_scope(root)
            self.assertFalse(path_decision(root/'link.txt', root, scope).allowed)
            red,status=redact_text('api_key="1234567890abcdef"')
            self.assertIn('<REDACTED>', red)
            self.assertFalse(payload_decision('DROP TABLE users', scope).allowed)
if __name__ == '__main__': unittest.main()
