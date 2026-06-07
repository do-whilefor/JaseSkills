import py_compile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class WindowsRuntimeEntryTest(unittest.TestCase):
    def test_windows_entry_files_and_preflight_script_compile(self):
        self.assertTrue((ROOT/'windows/run_skills.ps1').exists())
        self.assertTrue((ROOT/'windows/run_skills.cmd').exists())
        self.assertIn('powershell', (ROOT/'windows/run_skills.cmd').read_text(encoding='utf-8').lower())
        ps1 = (ROOT/'windows/run_skills.ps1').read_text(encoding='utf-8').lower()
        self.assertIn('using generated target-local default scope', ps1)
        self.assertNotIn('set-content -literalpath $scopefile', ps1)
        py_compile.compile(str(ROOT/'scripts/windows_preflight.py'), doraise=True)
if __name__=='__main__': unittest.main()
