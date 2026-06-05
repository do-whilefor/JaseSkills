#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/code-surface-inventory.py'
FIXTURE=ROOT/'tests/fixtures/python_app'

def test_code_surface_inventory_detects_routes_and_risks():
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'surface.jsonl'
        subprocess.run([sys.executable,str(SCRIPT),str(FIXTURE),'-o',str(out)],check=True,cwd=ROOT)
        rows=[json.loads(x) for x in out.read_text(encoding='utf-8').splitlines() if x.strip()]
    types={r['type'] for r in rows}
    assert 'flask_django_fastapi_route' in types
    assert 'upload_download' in types
    assert 'webhook' in types
    assert 'config_risk' in types
    assert 'dependency_or_deployment_manifest' in types
    assert all('asset_id' in r and 'source_file' in r and 'line' in r for r in rows)
