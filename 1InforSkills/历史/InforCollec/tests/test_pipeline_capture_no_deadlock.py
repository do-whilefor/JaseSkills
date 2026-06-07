from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests' / 'fixtures' / 'key_gap_app'


def test_js_collector_then_pipeline_capture_does_not_deadlock(tmp_path):
    """Regression for nested Node/Python subprocess capture on Windows-like runners."""
    js_out = tmp_path / 'js.json'
    first = subprocess.run(
        [sys.executable, 'collectors/js_asset_collector.py', '--input', str(FIX), '--scope', str(FIX), '--output', str(js_out), '--max-files', '100'],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
    )
    assert first.returncode == 0, first.stdout + first.stderr

    app = tmp_path / 'key_gap_app'
    shutil.copytree(FIX, app, symlinks=False)
    outside = tmp_path / 'outside.txt'
    outside.write_text('outside scope', encoding='utf-8')
    try:
        (app / 'runtime-created-outside-symlink').symlink_to(outside)
    except (OSError, NotImplementedError):
        pass

    pipe = tmp_path / 'pipe'
    second = subprocess.run(
        [sys.executable, 'info_end_run.py', '--input', str(app), '--scope', str(app), '--output', str(pipe), '--max-files', '200', '--cve-db', str(app / 'mock-cve-db.json')],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=180,
    )
    assert second.returncode == 0, second.stdout + second.stderr
    assert (pipe / 'collection-run.json').exists()
    assert (pipe / 'schema-validation.json').exists()
