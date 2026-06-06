#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/info-surface-normalizer.py'
FIXTURE=ROOT/'tests/fixtures/info_surface/static_candidates.jsonl'

def test_info_surface_normalizer_maps_fields_and_vulnerabilities():
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'normalized.jsonl'
        subprocess.run([sys.executable,str(SCRIPT),'--input',str(FIXTURE),'-o',str(out)],cwd=ROOT,check=True)
        rows=[json.loads(x) for x in out.read_text(encoding='utf-8').splitlines() if x.strip()]
    assert rows
    assert all(r['schema_version']=='info-surface' for r in rows)
    assert all('candidate_vulnerability' in r and 'review_status' in r and 'confidence' in r for r in rows)
    joined=' '.join(' '.join(r['candidate_vulnerability']) for r in rows)
    assert 'IDOR/BOLA' in joined
    assert 'tenant_isolation_bypass' in joined
    assert 'graphql_authorization_bypass' in joined
