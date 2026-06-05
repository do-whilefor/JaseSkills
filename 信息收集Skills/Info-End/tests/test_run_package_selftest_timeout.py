from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_selftest_runner_syntax_and_key_files_exist():
    shell = (ROOT/'scripts/run-package-selftest.sh').read_text(encoding='utf-8')
    assert 'selftest-step-runner.py' in shell
    source = (ROOT/'scripts/selftest-step-runner.py').read_text(encoding='utf-8')
    compile(source, str(ROOT/'scripts/selftest-step-runner.py'), 'exec')
    assert (ROOT/'detectors/c06_c30_high_impact_candidates.py').exists()
