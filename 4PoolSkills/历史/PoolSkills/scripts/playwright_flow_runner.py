#!/usr/bin/env python3
from __future__ import annotations
import asyncio, json, sys, datetime, hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse
from importlib.util import find_spec
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/dynamic_validation'; OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT/'scripts'))
from non_destructive_request_guard import check
SAFE_HOSTS={'127.0.0.1','localhost','::1'}
def now(): return datetime.datetime.utcnow().isoformat()+'Z'
def cid(x): return hashlib.sha256(x.encode()).hexdigest()[:16]
def allowed(url, allowed_hosts=None):
    host=urlparse(url).hostname or ''
    return host in set(allowed_hosts or []) | SAFE_HOSTS
async def run(plan_path):
    plan=json.loads(Path(plan_path).read_text(encoding='utf-8')); base=plan.get('base_url','http://127.0.0.1/'); dry=bool(plan.get('dry_run', True)); allowed_hosts=plan.get('allowed_hosts',['127.0.0.1','localhost'])
    role_matrix=plan.get('role_matrix',[{'role':'anonymous','credential_ref':None,'expected_access':'baseline'}])
    negative_controls=plan.get('negative_controls',[])
    if not allowed(base, allowed_hosts):
        out={'status':'validation_blocked','reason':'base_url outside local authorized scope','base_url':base}; (OUT/'flow_result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2)); return 2
    if find_spec('playwright') is None:
        out={'status':'validation_blocked','reason':'python playwright missing','tool':'playwright','impact':'browser flow cannot run; do not confirm dynamic vulnerabilities','role_matrix':role_matrix,'negative_controls':negative_controls}
        (OUT/'flow_result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2)); return 2
    if dry:
        out={'status':'dry_run','base_url':base,'steps':plan.get('steps',[]),'role_matrix':role_matrix,'negative_controls':negative_controls,'policy':'No browser launched in dry-run. Execute only after local authorization and tool health readiness.'}
        (OUT/'flow_result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2)); return 0
    from playwright.async_api import async_playwright
    events=[]; har_path=ROOT/plan.get('record_har_path','outputs/dynamic_validation/session.har'); har_path.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True); context=await browser.new_context(record_har_path=str(har_path)); page=await context.new_page()
        for role in role_matrix:
            for step in plan.get('steps',[]):
                if step.get('action')=='goto':
                    url=urljoin(base, step.get('url','/'))
                    if not allowed(url, allowed_hosts): events.append({'role':role.get('role'),'step':step,'blocked':'outside_allowed_hosts'}); continue
                    g=check('GET',url,dry_run=False)
                    if g['status']!='allow': events.append({'role':role.get('role'),'step':step,'blocked':g}); continue
                    resp=await page.goto(url); events.append({'role':role.get('role'),'action':'goto','status':resp.status if resp else None,'url':url,'timestamp':now()})
                elif step.get('action')=='screenshot':
                    sp=ROOT/step.get('path',f'outputs/dynamic_validation/{role.get("role","role")}.png'); sp.parent.mkdir(parents=True, exist_ok=True); await page.screenshot(path=str(sp)); events.append({'role':role.get('role'),'screenshot_path':str(sp),'timestamp':now()})
        await context.close(); await browser.close()
    c='dyn-'+cid(base+str(events))
    manifest={'manifest_version':'4.0','generated_at':now(),'scope':{'mode':'local_authorized','project_root':str(ROOT),'allowed_hosts':allowed_hosts,'forbidden_actions':['destructive_state_change','dos','third_party_targeting']},'candidates':[{'id':c,'type':'dynamic_observation','severity':'info','status':'needs_review','source':'dynamic','route':base,'method':'GET','parameter':None,'auth_context':{},'tenant_context':{},'role_matrix':role_matrix,'tenant_matrix':plan.get('tenant_matrix',[]),'code_evidence':[],'js_evidence':[],'dynamic_evidence':[{'id':c+'-browser','source':'playwright','route':base,'method':'GET','har_path':str(har_path),'summary':'Playwright non-destructive browser flow captured HAR/screenshots where configured'}],'negative_controls':negative_controls,'state_history':[{'from':None,'to':'reproduced','reason':'browser flow executed as observation','timestamp':now()}],'impact_proof':{},'false_positive_exclusions':['dynamic flow alone does not prove vulnerability'],'quality_gate':{'score':0,'status':'needs_review','hard_failures':['missing_code_evidence','missing_confirmed_impact']},'report_mapping':{},'non_destructive':{'is_non_destructive':True,'data_modified':False,'boundary':'GET/screenshot only unless plan explicitly extends with local authorization'}}]}
    (OUT/'evidence_manifest_v4.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    out={'status':'reproduced' if events else 'validation_blocked','events':events,'har_path':str(har_path),'manifest':str(OUT/'evidence_manifest_v4.json')}
    (OUT/'flow_result.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2)); return 0
if __name__=='__main__': raise SystemExit(asyncio.run(run(sys.argv[1] if len(sys.argv)>1 else ROOT/'config/dynamic_flow_plan.example.json')))
