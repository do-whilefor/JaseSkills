import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_clean_release_artifacts_removes_cache_not_templates_or_knowledge(tmp_path):
    work=tmp_path/'pkg'
    subprocess.run(['cp','-a',str(ROOT)+'/.', str(work)], check=True)
    (work/'.pytest_cache').mkdir(exist_ok=True)
    (work/'selftest/out').mkdir(parents=True, exist_ok=True)
    (work/'selftest/out/stale.txt').write_text('stale')
    subprocess.run(['bash', str(work/'scripts/clean-release-artifacts.sh'), str(work)], check=True)
    assert not (work/'.pytest_cache').exists()
    assert not (work/'selftest/out').exists()
    assert (work/'templates').exists()
    assert (work/'knowledge').exists()
