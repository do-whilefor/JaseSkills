#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/js-asset-audit.py'
FIXTURE=ROOT/'tests/fixtures/js_app'

def run_script():
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'out.jsonl'
        subprocess.run([sys.executable,str(SCRIPT),str(FIXTURE),'-o',str(out)],check=True,cwd=ROOT)
        return [json.loads(x) for x in out.read_text(encoding='utf-8').splitlines() if x.strip()]

def test_detects_core_js_assets():
    rows=run_script(); types={r['type'] for r in rows}
    assert 'html_script_src' in types
    assert 'inline_script' in types
    assert 'dynamic_import_chunk' in types
    assert 'sourcemap_hint' in types
    assert 'request_wrapper_hint' in types
    assert 'url_or_endpoint_literal' in types
    assert 'graphql_operation_hint' in types
    assert 'auth_material_flow_hint' in types
    assert 'parameter_source_hint' in types
    assert 'source_sink_candidate_hint' in types
    assert all('source_file' in r and 'line' in r for r in rows)
    assert all(r['dynamic_status']=='not_validated' for r in rows)
