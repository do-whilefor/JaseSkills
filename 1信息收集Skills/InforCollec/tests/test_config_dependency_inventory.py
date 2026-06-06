#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/config-dependency-inventory.py'
FIXTURE=ROOT/'tests/fixtures/config_app'

def test_config_dependency_inventory_extracts_dependencies_and_risks():
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'config.jsonl'
        subprocess.run([sys.executable,str(SCRIPT),str(FIXTURE),'-o',str(out)],cwd=ROOT,check=True)
        rows=[json.loads(x) for x in out.read_text(encoding='utf-8').splitlines() if x.strip()]
    types={r['type'] for r in rows}
    assert 'dependency_manifest' in types
    assert 'dependency_entry' in types
    assert 'dependency_script_candidate' in types
    assert 'debug_enabled' in types
    assert 'cors_candidate' in types
    assert 'object_storage_candidate' in types
    assert all('source_file' in r and 'line' in r and 'asset_id' in r for r in rows)
