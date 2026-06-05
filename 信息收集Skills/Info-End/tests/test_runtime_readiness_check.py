#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_runtime_readiness_required_files_pass():
    r=subprocess.run([sys.executable,'scripts/runtime-readiness-check.py','--project-root','.','--base-url','http://localhost:3000'],cwd=ROOT,stdout=subprocess.PIPE,text=True,check=True)
    data=json.loads(r.stdout)
    assert data['status']=='PASS'
    assert all(data['required_package_files'].values())
    assert data['base_url_checks'][0]['default_local_allowed'] is True
