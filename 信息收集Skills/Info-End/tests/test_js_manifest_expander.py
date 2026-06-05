#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/js-manifest-expander.py'
FIXTURE=ROOT/'tests/fixtures/js_app'

def test_js_manifest_expander_finds_manifest_worker_assets():
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'manifest.jsonl'
        subprocess.run([sys.executable,str(SCRIPT),str(FIXTURE),'-o',str(out)],cwd=ROOT,check=True)
        rows=[json.loads(x) for x in out.read_text(encoding='utf-8').splitlines() if x.strip()]
    types={r['type'] for r in rows}
    assert 'frontend_manifest_asset' in types
    assert 'service_worker_or_precache_file' in types
    assert 'service_worker_cache_hint' in types
    assert any('/static/lazy-admin.js' in str(r.get('value')) for r in rows)
