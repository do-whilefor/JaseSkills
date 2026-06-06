from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_clean_package_has_no_update_reports_or_stale_selftest_outputs():
    forbidden_exact = ['FINAL_FILE_HASHES.json', 'REPAIRED_FILE_HASHES.json', 'docs/version-changelog.md', 'selftest/out']
    forbidden_patterns = ['*REPAIR_REPORT*.md', '*HARDENING*.md', '*FINAL_FIX*.md', '*SECOND_PASS*.md', '*EXTREME_AUDIT*.md']
    assert not [p for p in forbidden_exact if (ROOT/p).exists()]
    hits=[]
    for pattern in forbidden_patterns:
        hits.extend(ROOT.glob(f'docs/{pattern}'))
    assert not hits

def test_stable_clean_paths_exist():
    assert (ROOT/'templates/unified-quality-gate.md').exists()
    assert (ROOT/'examples/regression-test-suite.md').exists()
    assert (ROOT/'docs/trigger-routing.md').exists()
