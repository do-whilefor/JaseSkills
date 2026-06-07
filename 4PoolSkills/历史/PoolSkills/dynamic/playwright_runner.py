#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime, importlib.util, json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import load_scope, assert_url_allowed, assert_payload_safe, ScopeError, load_yaml

def now(): return datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')

def _rel(p: Path, root: Path) -> str:
    try: return str(p.resolve().relative_to(root.resolve())).replace('\\','/')
    except Exception: return str(p)

def _join_url(base: str, path_or_url: str | None) -> str:
    if not path_or_url: return base
    if urllib.parse.urlparse(path_or_url).scheme: return path_or_url
    return urllib.parse.urljoin(base.rstrip('/')+'/', path_or_url.lstrip('/'))

def load_matrix(matrix_file: str | None):
    p=Path(matrix_file) if matrix_file else Path(__file__).with_name('role_tenant_matrix.yaml')
    data=load_yaml(p)
    roles=data.get('roles') or ['anonymous']
    tenants=data.get('tenants') or ['default']
    accounts=data.get('accounts') or {}
    login=data.get('login') or {}
    tenant_switch=data.get('tenant_switch') or {}
    return {'schema_version':data.get('version','role-tenant-matrix-v1'),'roles':roles,'tenants':tenants,'accounts':accounts,'login':login,'tenant_switch':tenant_switch,'policy':data.get('policy',{})}

def _planned_roles_tenants(plan, matrix, selected_role=None, selected_tenant=None, full_matrix=False):
    roles=[selected_role] if selected_role else matrix['roles']
    tenants=[selected_tenant] if selected_tenant else matrix['tenants']
    if not (plan.get('full_matrix') or full_matrix) and not selected_role and not selected_tenant:
        roles=roles[:2]; tenants=tenants[:2]
    return [(r,t) for r in roles for t in tenants]

def _validate_plan_payloads(plans, scope):
    blocked=[]; verified_block_controls=[]
    for plan in plans:
        for st in plan.get('steps',[]):
            payload=str(st.get('payload',''))
            try:
                assert_payload_safe(payload, scope)
            except ScopeError as e:
                if st.get('action') == 'blocked_control':
                    verified_block_controls.append({'finding_id':plan.get('finding_id'),'replay_plan_id':plan.get('replay_plan_id'),'step':st.get('id'),'status':'blocked_control_verified','error':str(e)})
                else:
                    blocked.append({'finding_id':plan.get('finding_id'),'replay_plan_id':plan.get('replay_plan_id'),'step':st.get('id'),'error':str(e)})
    return blocked, verified_block_controls

def _write_json(path: Path, data) -> str:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return str(path)

def _value_from_account(value: str | None, account: dict) -> str:
    if not isinstance(value, str): return '' if value is None else str(value)
    if value.startswith('$account.'):
        return str(account.get(value.split('.',1)[1], ''))
    return value

def _perform_login(page, context, target_url: str, matrix: dict, role: str, tenant: str, storage_dir: Path, root: Path, errors: list[str]) -> str | None:
    account=(matrix.get('accounts') or {}).get(role) or {}
    state_file=storage_dir/f'{role}_{tenant}.json'
    if state_file.exists():
        return str(state_file)
    login=matrix.get('login') or {}
    steps=login.get('steps') or account.get('login_steps') or []
    if not steps:
        return None
    login_url=_join_url(target_url, login.get('url') or account.get('login_url') or '/login')
    page.goto(login_url, wait_until='networkidle', timeout=int(login.get('timeout_ms') or 15000))
    for st in steps:
        action=st.get('action')
        selector=st.get('selector')
        if action=='fill' and selector:
            page.fill(selector, _value_from_account(st.get('value'), account), timeout=5000)
        elif action=='click' and selector:
            page.click(selector, timeout=5000)
        elif action=='press' and selector:
            page.press(selector, st.get('key','Enter'), timeout=5000)
        elif action=='wait_for_url' and st.get('url'):
            page.wait_for_url(st['url'], timeout=int(st.get('timeout_ms') or 10000))
        elif action=='wait_for_selector' and selector:
            page.wait_for_selector(selector, timeout=int(st.get('timeout_ms') or 10000))
        elif action=='goto' and st.get('url'):
            page.goto(_join_url(target_url, st['url']), wait_until='networkidle', timeout=15000)
    context.storage_state(path=str(state_file))
    return str(state_file)

def _perform_tenant_switch(page, target_url: str, matrix: dict, tenant: str):
    cfg=matrix.get('tenant_switch') or {}
    steps=cfg.get('steps') or []
    for st in steps:
        action=st.get('action')
        selector=st.get('selector')
        value=str(st.get('value','')).replace('$tenant', tenant)
        if action=='click' and selector:
            page.click(selector, timeout=5000)
        elif action=='fill' and selector:
            page.fill(selector, value, timeout=5000)
        elif action=='select' and selector:
            page.select_option(selector, value, timeout=5000)
        elif action=='goto' and st.get('url'):
            page.goto(_join_url(target_url, st['url'].replace('$tenant', tenant)), wait_until='networkidle', timeout=15000)

def _execute_http_control(context, target_url: str, scope, step: dict, prefix: str, artifact_dir: Path, root: Path, kind: str) -> tuple[str, str | None, str | None, list[str]]:
    errors=[]
    method=str(step.get('method') or 'GET').upper()
    url=_join_url(target_url, step.get('url') or step.get('path') or '/')
    assert_url_allowed(url, scope)
    payload=step.get('payload')
    if payload is not None: assert_payload_safe(str(payload), scope)
    headers=step.get('headers') or {}
    req_path=artifact_dir/f'{prefix}.{kind}.request.json'
    res_path=artifact_dir/f'{prefix}.{kind}.response.json'
    req_data={'method':method,'url':url,'headers':headers,'payload':payload,'step_id':step.get('id'),'kind':kind}
    _write_json(req_path, req_data)
    try:
        resp=context.request.fetch(url, method=method, headers=headers, data=payload if isinstance(payload,str) else None, timeout=int(step.get('timeout_ms') or 10000))
        text=''
        try: text=resp.text()[:20000]
        except Exception: text=''
        res_data={'url':url,'status':resp.status,'headers':dict(resp.headers),'body_prefix':text,'step_id':step.get('id'),'kind':kind}
        _write_json(res_path, res_data)
        expected=step.get('expected_status')
        forbidden_status=step.get('forbidden_status')
        status='passed'
        if expected is not None and int(resp.status) != int(expected): status='failed'
        if forbidden_status is not None and int(resp.status) == int(forbidden_status): status='failed'
        if step.get('body_must_not_contain') and step['body_must_not_contain'] in text: status='failed'
        return status, _rel(req_path, root), _rel(res_path, root), errors
    except Exception as e:
        errors.append(str(e))
        _write_json(res_path, {'status':'request_failed','error':str(e),'step_id':step.get('id'),'kind':kind})
        return 'failed', _rel(req_path, root), _rel(res_path, root), errors

def _run_plan_steps(page, context, plan: dict, target_url: str, scope, prefix: str, artifact_dir: Path, root: Path):
    neg_status='not_applicable'
    blocked_status='not_applicable'
    control_refs={}
    errors=[]
    for st in plan.get('steps',[]):
        action=st.get('action')
        selector=st.get('selector')
        try:
            if action == 'click' and selector:
                page.click(selector, timeout=5000)
            elif action == 'fill' and selector:
                page.fill(selector, str(st.get('value','')), timeout=5000)
            elif action == 'goto' and st.get('url'):
                url=_join_url(target_url, st['url']); assert_url_allowed(url, scope); page.goto(url, wait_until='networkidle', timeout=15000)
            elif action == 'trigger_lazy_load':
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(int(st.get('wait_ms') or 1000))
            elif action == 'negative_control':
                neg_status='not_executed'
                if st.get('url') or st.get('path'):
                    neg_status, rq, rs, errs=_execute_http_control(context,target_url,scope,st,prefix,artifact_dir,root,'negative')
                    control_refs['negative_request_ref']=rq; control_refs['negative_response_ref']=rs; errors.extend(errs)
            elif action == 'blocked_control':
                blocked_status='not_executed'
                try:
                    assert_payload_safe(str(st.get('payload','')), scope)
                    if st.get('url') or st.get('path'):
                        blocked_status, rq, rs, errs=_execute_http_control(context,target_url,scope,st,prefix,artifact_dir,root,'blocked')
                        control_refs['blocked_request_ref']=rq; control_refs['blocked_response_ref']=rs; errors.extend(errs)
                    else:
                        blocked_status='passed'
                except ScopeError as e:
                    blocked_status='blocked_expected'; errors.append('blocked_control_verified:'+str(e))
            elif action in {'review_source_context'}:
                continue
        except Exception as e:
            errors.append(f'{action}:{e}')
            if action == 'negative_control': neg_status='failed'
            if action == 'blocked_control': blocked_status='failed'
    return neg_status, blocked_status, control_refs, errors

def _run_playwright(plans, root: Path, scope, target_url: str, artifact_dir: Path, storage_dir: Path, matrix, selected_role=None, selected_tenant=None, headless=True, full_matrix=False):
    from playwright.sync_api import sync_playwright  # type: ignore
    artifact_dir.mkdir(parents=True,exist_ok=True); storage_dir.mkdir(parents=True,exist_ok=True)
    results=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=headless)
        try:
            for plan in plans:
                plan_results=[]
                for role,tenant in _planned_roles_tenants(plan,matrix,selected_role,selected_tenant,full_matrix):
                    safe_role=str(role).replace('/','_').replace('\\','_')
                    safe_tenant=str(tenant).replace('/','_').replace('\\','_')
                    prefix=f"{plan.get('replay_plan_id','rp')}_{safe_role}_{safe_tenant}"
                    har=artifact_dir/f'{prefix}.har'
                    trace=artifact_dir/f'{prefix}.zip'
                    screenshot=artifact_dir/f'{prefix}.png'
                    dom=artifact_dir/f'{prefix}.dom.html'
                    console_file=artifact_dir/f'{prefix}.console.json'
                    network_file=artifact_dir/f'{prefix}.network.json'
                    request_file=artifact_dir/f'{prefix}.request.json'
                    response_file=artifact_dir/f'{prefix}.response.json'
                    state_file=storage_dir/f'{safe_role}_{safe_tenant}.json'
                    storage_state=str(state_file) if state_file.exists() else None
                    requests=[]; responses=[]; consoles=[]; errors=[]
                    context=browser.new_context(storage_state=storage_state, record_har_path=str(har))
                    context.tracing.start(screenshots=True, snapshots=True, sources=True)
                    page=context.new_page()
                    page.on('console', lambda msg, bag=consoles: bag.append({'type':msg.type,'text':msg.text[:1000]}))
                    page.on('request', lambda req, bag=requests: bag.append({'method':req.method,'url':req.url,'resource_type':req.resource_type,'headers':dict(req.headers)}))
                    page.on('response', lambda resp, bag=responses: bag.append({'url':resp.url,'status':resp.status,'headers':dict(resp.headers)}))
                    status='passed'; neg_status='not_applicable'; blocked_status='not_applicable'; control_refs={}
                    try:
                        _perform_login(page, context, target_url, matrix, role, tenant, storage_dir, root, errors)
                        page.goto(target_url, wait_until='networkidle', timeout=int(plan.get('timeout_ms') or 15000))
                        _perform_tenant_switch(page, target_url, matrix, tenant)
                        neg_status, blocked_status, control_refs, step_errors = _run_plan_steps(page, context, plan, target_url, scope, prefix, artifact_dir, root)
                        errors.extend(step_errors)
                        page.screenshot(path=str(screenshot), full_page=True)
                        dom.write_text(page.content(), encoding='utf-8')
                        console_file.write_text(json.dumps(consoles,ensure_ascii=False,indent=2), encoding='utf-8')
                        network_file.write_text(json.dumps({'requests':requests,'responses':responses},ensure_ascii=False,indent=2), encoding='utf-8')
                        request_file.write_text(json.dumps(requests,ensure_ascii=False,indent=2), encoding='utf-8')
                        response_file.write_text(json.dumps(responses,ensure_ascii=False,indent=2), encoding='utf-8')
                        context.storage_state(path=str(state_file))
                        if neg_status == 'failed' or blocked_status == 'failed': status='not_reproducible'
                    except Exception as e:
                        status='needs_review'; errors.append(str(e))
                    finally:
                        try: context.tracing.stop(path=str(trace))
                        except Exception as e: errors.append('trace_stop:'+str(e))
                        context.close()
                    has_request=bool(requests) or request_file.exists()
                    has_response=bool(responses) or response_file.exists()
                    has_visual=screenshot.exists() or dom.exists()
                    rec={'role':role,'tenant':tenant,'status':status,'request_ref':_rel(request_file,root) if request_file.exists() else None,'response_ref':_rel(response_file,root) if response_file.exists() else None,'screenshot_ref':_rel(screenshot,root) if screenshot.exists() else None,'trace_ref':_rel(trace,root) if trace.exists() else None,'har_ref':_rel(har,root) if har.exists() else None,'console_ref':_rel(console_file,root) if console_file.exists() else None,'dom_ref':_rel(dom,root) if dom.exists() else None,'network_ref':_rel(network_file,root) if network_file.exists() else None,'errors':errors,'negative_status':neg_status,'blocked_status':blocked_status,'control_refs':control_refs,'checks':{'request':has_request,'response':has_response,'screenshot_or_dom':has_visual}}
                    plan_results.append(rec)
                best=next((x for x in plan_results if x['status']=='passed' and x['request_ref'] and x['response_ref'] and (x['screenshot_ref'] or x['dom_ref'])), plan_results[0] if plan_results else {})
                results.append({'finding_id':plan.get('finding_id'),'replay_plan_id':plan.get('replay_plan_id'),'status':best.get('status','needs_review'),'role':best.get('role'),'tenant':best.get('tenant'),'request_ref':best.get('request_ref'),'response_ref':best.get('response_ref'),'screenshot_ref':best.get('screenshot_ref'),'trace_ref':best.get('trace_ref'),'har_ref':best.get('har_ref'),'console_ref':best.get('console_ref'),'dom_ref':best.get('dom_ref'),'matrix_results':plan_results,'errors':best.get('errors',[]),'negative_status':best.get('negative_status','not_executed'),'blocked_status':best.get('blocked_status','not_executed'),'control_refs':best.get('control_refs',{})})
        finally:
            browser.close()
    return results

def run(plan_file, root='.', target_url=None, scope_file=None, matrix_file=None, artifact_dir=None, storage_dir=None, role=None, tenant=None, headless=True, full_matrix=False):
    root=Path(root).resolve(); scope=load_scope(root,scope_file); plans=json.loads(Path(plan_file).read_text(encoding='utf-8')).get('plans',[])
    if target_url: assert_url_allowed(target_url, scope)
    blocked, verified_block_controls=_validate_plan_payloads(plans, scope)
    playwright_available = importlib.util.find_spec('playwright') is not None
    matrix=load_matrix(matrix_file)
    if blocked:
        results=[{'finding_id':b.get('finding_id'),'replay_plan_id':b.get('replay_plan_id'),'status':'blocked','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None,'matrix_results':[],'errors':[b['error']],'negative_status':'not_executed','blocked_status':'blocked_expected'} for b in blocked]
    elif not playwright_available:
        results=[{'finding_id':p.get('finding_id'),'replay_plan_id':p.get('replay_plan_id'),'status':'unavailable','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None,'matrix_results':[],'errors':['playwright_python_package_missing'],'negative_status':'not_executed','blocked_status':'not_executed'} for p in plans]
    elif not target_url:
        results=[{'finding_id':p.get('finding_id'),'replay_plan_id':p.get('replay_plan_id'),'status':'needs_manual_target','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None,'matrix_results':[],'errors':['target_url_required'],'negative_status':'not_executed','blocked_status':'not_executed'} for p in plans]
    else:
        try:
            results=_run_playwright(plans, root, scope, target_url, Path(artifact_dir or root/'evidence/dynamic'), Path(storage_dir or root/'dynamic/storage_states'), matrix, role, tenant, headless=headless, full_matrix=full_matrix)
        except Exception as e:
            # Playwright may be importable while its browser binaries are missing,
            # especially on fresh Windows installs before `python -m playwright install chromium`.
            # Emit a schema-valid replay result instead of crashing the pipeline.
            results=[{'finding_id':p.get('finding_id'),'replay_plan_id':p.get('replay_plan_id'),'status':'unavailable','request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None,'matrix_results':[],'errors':['playwright_runtime_unavailable:'+str(e)],'negative_status':'not_executed','blocked_status':'not_executed'} for p in plans]
    return {'schema_version':'replay-result-v2','generated_at':now(),'playwright_available':playwright_available,'role_tenant_matrix':matrix,'results':results,'blocked_controls':verified_block_controls,'policy':'Runner captures scoped HAR/trace/screenshot/DOM/console/request/response and executes login, tenant switching, positive/negative/blocked controls when target_url and matrix are provided. Quality gate, not runner, decides confirmed.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',required=True); ap.add_argument('--root',default='.'); ap.add_argument('--target-url'); ap.add_argument('--scope-file'); ap.add_argument('--matrix'); ap.add_argument('--artifact-dir'); ap.add_argument('--storage-dir'); ap.add_argument('--role'); ap.add_argument('--tenant'); ap.add_argument('--headed',action='store_true'); ap.add_argument('--full-matrix',action='store_true'); ap.add_argument('--out',required=True)
    ns=ap.parse_args(); data=run(ns.plan,ns.root,ns.target_url,ns.scope_file,ns.matrix,ns.artifact_dir,ns.storage_dir,ns.role,ns.tenant,headless=not ns.headed,full_matrix=ns.full_matrix)
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'results':len(data['results']),'playwright_available':data['playwright_available']},ensure_ascii=False))
if __name__=='__main__': main()
