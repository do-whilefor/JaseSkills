#!/usr/bin/env python3
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/dynamic_validation'; OUT.mkdir(parents=True,exist_ok=True)
def build():
    idx=ROOT/'auth_contexts/auth_contexts.index.json'; contexts=json.loads(idx.read_text(encoding='utf-8')).get('contexts',[]) if idx.exists() else []
    tests=[]
    for a in contexts:
        for b in contexts:
            relation='same_tenant' if a.get('tenant')==b.get('tenant') else 'cross_tenant'
            tests.append({'actor_context':a.get('id'),'target_context':b.get('id'),'relation':relation,'expected_boundary':'deny' if relation=='cross_tenant' and a.get('role')!='admin' else 'allow_or_app_policy','status':'validation_planned'})
    out={'status':'ok' if tests else 'validation_blocked','reason':None if tests else 'no auth contexts registered','tests':tests,'policy':'Plan only; use Playwright runner and non-destructive guard for execution.'}
    (OUT/'role_matrix_plan.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': build()
