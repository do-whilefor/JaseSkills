#!/usr/bin/env python3
"""Adversarial harness: false dynamic-validation claims must fail."""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
GUARD=ROOT/'_shared/quality/final_claim_guard.py'

def write(p: Path, obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')

def run_case(name: str, claim_level: str, files: dict[str,dict]):
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); paths={}
        for k,obj in files.items():
            pp=td/(k+'.json'); write(pp,obj); paths[k]=pp
        cmd=[sys.executable,str(GUARD),'--claim-level',claim_level]
        if 'manifest' in paths: cmd += ['--manifest',str(paths['manifest'])]
        if 'browser' in paths: cmd += ['--browser-coverage',str(paths['browser'])]
        if 'lazy' in paths: cmd += ['--lazy-js-ledger',str(paths['lazy'])]
        if 'matrix' in paths: cmd += ['--role-tenant-matrix',str(paths['matrix'])]
        if 'variant' in paths: cmd += ['--variant-expansion',str(paths['variant'])]
        cp=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        try: out=json.loads(cp.stdout)
        except Exception: out={'parse_error':cp.stdout,'stderr':cp.stderr}
        return {'name':name,'expected_block':True,'blocked':cp.returncode != 0,'returncode':cp.returncode,'blockers':out.get('blockers',[])}

def main():
    fake_browser={'schema_version':'browser_interaction_coverage_v1','runtime_status':'planned_only','browser_executed':False,'observed_actions':[]}
    fake_lazy={'schema_version':'lazy_js_asset_ledger_v1','files_scanned':10,'browser_trigger_required':2,'browser_trigger_status':'not_executed'}
    fake_matrix={'roles':[],'tenants':[],'test_case_count':0,'status':'planned_only_until_executed'}
    fake_variant={'candidate_count':1,'expansions':[]}
    fake_manifest={'schema_version':'evidence_manifest_v5','status':'missing_required_evidence'}
    cases=[
        run_case('confirmed_without_browser_or_matrix','confirmed',{'browser':fake_browser,'lazy':fake_lazy,'matrix':fake_matrix,'variant':fake_variant,'manifest':fake_manifest}),
        run_case('dynamic_complete_without_actions','dynamic_complete',{'browser':fake_browser}),
        run_case('full_frontend_without_lazy_trigger','full_frontend_coverage',{'browser':fake_browser,'lazy':fake_lazy}),
    ]
    passed=all(c['blocked'] for c in cases)
    result={'schema_version':'top_tier_adversarial_harness_v1','passed':passed,'cases':cases,'policy':'false dynamic or confirmed claims must be blocked'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if passed else 1
if __name__=='__main__': raise SystemExit(main())
