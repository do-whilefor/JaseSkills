#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_evidence_schema_validator_accepts_generated_manifest():
    with tempfile.TemporaryDirectory() as td:
        out=Path(td)/'manifest.json'
        subprocess.run([sys.executable,'scripts/report-to-manifest.py','--project-name','unit','--project-root','.','--extra-file','README.md','--out',str(out)],cwd=ROOT,check=True)
        r=subprocess.run([sys.executable,'scripts/evidence-schema-validate.py',str(out),'--kind','evidence-manifest'],cwd=ROOT,stdout=subprocess.PIPE,text=True,check=True)
        assert json.loads(r.stdout)['status']=='PASS'
