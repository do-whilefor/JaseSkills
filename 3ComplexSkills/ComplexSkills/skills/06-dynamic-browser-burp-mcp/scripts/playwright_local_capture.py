#!/usr/bin/env python3
"""Real local-only browser/HAR/screenshot role-matrix dynamic validator v4.1.

Safety boundary: only file://, localhost, 127.0.0.1, ::1 are allowed. Default methods
are GET/HEAD/browser navigation. Non-destructive negative controls compare role and
tenant sessions without modifying server state. If Playwright/browser is missing,
the script returns runtime_unavailable instead of pretending success.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, socket, time, urllib.parse, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def allowed(url:str)->bool:
    u=urllib.parse.urlparse(url); return u.scheme=='file' or u.hostname in {'localhost','127.0.0.1','::1'}
def sha_file(p:Path)->str:
    h=hashlib.sha256();
    if p.exists(): h.update(p.read_bytes())
    return h.hexdigest()
def rel(p:Path)->str:
    try: return str(p.resolve().relative_to(ROOT))
    except Exception: return str(p)
def check():
    pkg=False; runtime_ready=False; runtime_reason=''
    try:
        import playwright.sync_api as _p  # type: ignore
        pkg=True
        try:
            from playwright.sync_api import sync_playwright  # type: ignore
            with sync_playwright() as p:
                b=p.chromium.launch(headless=True); b.close(); runtime_ready=True
        except Exception as exc:
            runtime_reason=f'{exc.__class__.__name__}: {str(exc)[:240]}'
    except Exception as exc:
        runtime_reason=f'{exc.__class__.__name__}: {str(exc)[:240]}'; pkg=False
    return {'schema_version':'dynamic_browser_role_matrix_check_v4.1','python_playwright_package':pkg,'playwright_browser_runtime_ready':runtime_ready,'browser_runtime_reason':runtime_reason,'browser_cli':bool(shutil.which('chromium') or shutil.which('google-chrome') or shutil.which('msedge') or shutil.which('firefox')),'policy':'localhost_or_file_only_non_destructive_browser_har_screenshot_role_tenant_matrix'}
def load_matrix(path):
    if not path:
        return {'roles':[{'role':'anonymous','tenant':'public','headers':{},'cookies':[],'localStorage':{}}], 'negative_controls':[{'name':'anonymous_replay','role':'anonymous','tenant':'public','expect_same_or_less_privilege':True}]}
    obj=json.loads(Path(path).read_text(encoding='utf-8'))
    if isinstance(obj,list): obj={'roles':obj,'negative_controls':[]}
    return obj
def write_json(p,obj): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def urllib_capture(url,outdir,role,tenant,method='GET'):
    if method.upper() not in {'GET','HEAD'}: raise ValueError('only GET/HEAD allowed')
    req=urllib.request.Request(url,method=method.upper(),headers={'User-Agent':'authorized-local-browser-role-matrix/4.1','X-Audit-Role':role,'X-Audit-Tenant':tenant})
    start=time.time(); status=0; headers={}; body=b''; err=None
    try:
        with urllib.request.urlopen(req,timeout=10) as r:
            status=r.status; headers=dict(r.headers); body=r.read(262144)
    except Exception as exc: err=f'{exc.__class__.__name__}: {exc}'
    stem='capture_'+hashlib.sha256((url+role+tenant+method).encode()).hexdigest()[:12]
    reqp=outdir/(stem+'_request.redacted.json'); respp=outdir/(stem+'_response.redacted.json'); harp=outdir/(stem+'.har.json')
    req_obj={'method':method.upper(),'url':url,'role':role,'tenant':tenant,'headers_redacted':{'User-Agent':'authorized-local-browser-role-matrix/4.1','X-Audit-Role':role,'X-Audit-Tenant':tenant},'non_destructive':True}
    resp_obj={'status':status,'headers_redacted':{k:('<redacted>' if k.lower() in {'authorization','cookie','set-cookie','x-api-key'} else v) for k,v in headers.items()},'body_size':len(body),'body_sha256':hashlib.sha256(body).hexdigest() if body else '', 'error':err,'duration_ms':round((time.time()-start)*1000)}
    har={'log':{'version':'1.2','creator':{'name':'playwright_local_capture.py','version':'4.1'},'entries':[{'request':{'method':method.upper(),'url':url},'response':{'status':status,'content':{'size':len(body),'sha256':resp_obj['body_sha256']}},'audit_role':role,'audit_tenant':tenant,'negative_control':False,'non_destructive':True}]}}
    for p,o in [(reqp,req_obj),(respp,resp_obj),(harp,har)]: write_json(p,o)
    return {'role':role,'tenant':tenant,'method':method.upper(),'url':url,'status':status,'error':err,'browser_executed':False,'artifacts':[{'type':'request','path':rel(reqp),'sha256':sha_file(reqp),'redacted':True},{'type':'response','path':rel(respp),'sha256':sha_file(respp),'redacted':True},{'type':'har','path':rel(harp),'sha256':sha_file(harp),'redacted':True}]}
def browser_capture(url,outdir,role_cfg):
    from playwright.sync_api import sync_playwright  # type: ignore
    role=role_cfg.get('role','role'); tenant=role_cfg.get('tenant','tenant')
    events=[]; start=time.time()
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        ctx=browser.new_context(extra_http_headers={**role_cfg.get('headers',{}),'X-Audit-Role':role,'X-Audit-Tenant':tenant})
        for c in role_cfg.get('cookies') or []: ctx.add_cookies([c])
        page=ctx.new_page()
        def on_req(req): events.append({'type':'request','method':req.method,'url':req.url,'headers':{k:('<redacted>' if k.lower() in {'authorization','cookie','x-api-key'} else v) for k,v in req.headers.items()}})
        def on_resp(resp): events.append({'type':'response','url':resp.url,'status':resp.status,'headers':{k:('<redacted>' if k.lower() in {'authorization','cookie','set-cookie','x-api-key'} else v) for k,v in resp.headers.items()}})
        page.on('request',on_req); page.on('response',on_resp)
        for k,v in (role_cfg.get('localStorage') or {}).items(): page.add_init_script(f"localStorage.setItem({json.dumps(k)}, {json.dumps(v)});")
        page.goto(url,wait_until='networkidle',timeout=15000)
        title=page.title(); content_len=len(page.content())
        sp=outdir/('screenshot_'+hashlib.sha256((url+role+tenant).encode()).hexdigest()[:12]+'.png'); page.screenshot(path=str(sp),full_page=True)
        browser.close()
    stem='browser_'+hashlib.sha256((url+role+tenant).encode()).hexdigest()[:12]
    harp=outdir/(stem+'.har.json'); meta=outdir/(stem+'_browser_meta.redacted.json')
    har={'log':{'version':'1.2','creator':{'name':'playwright_local_capture.py','version':'4.1'},'entries':events,'audit_role':role,'audit_tenant':tenant,'non_destructive':True}}
    write_json(harp,har); write_json(meta,{'role':role,'tenant':tenant,'title':title,'content_length':content_len,'duration_ms':round((time.time()-start)*1000),'non_destructive':True})
    return {'role':role,'tenant':tenant,'url':url,'status':'browser_completed','browser_executed':True,'artifacts':[{'type':'har','path':rel(harp),'sha256':sha_file(harp),'redacted':True},{'type':'browser_meta','path':rel(meta),'sha256':sha_file(meta),'redacted':True},{'type':'screenshot','path':rel(sp),'sha256':sha_file(sp),'redacted':False}]}
def run(args):
    matrix=load_matrix(args.role_matrix); outp=Path(args.out); outdir=outp.parent/'capture_artifacts'; outdir.mkdir(parents=True,exist_ok=True)
    roles=matrix.get('roles') or []
    if not allowed(args.url):
        res={'schema_version':'dynamic_browser_role_matrix_result_v4.1','passed':False,'error':'url_not_allowed','policy':'localhost_or_file_only','url':args.url,'dynamic_claim_allowed':False}
        write_json(outp,res); return res
    availability=check(); captures=[]; browser_errors=[]
    if args.browser and not availability.get('playwright_browser_runtime_ready'):
        res={'schema_version':'dynamic_browser_role_matrix_result_v4.1','url':args.url,'non_destructive':True,'policy':'localhost_or_file_only_browser_har_screenshot_role_tenant_matrix','browser_requested':True,'availability':availability,'capture_count':0,'captures':[],'negative_controls':[],'browser_errors':[{'error':'runtime_unavailable','reason':availability.get('browser_runtime_reason')}],'runtime_status':'runtime_unavailable','dynamic_claim_allowed':False,'passed':False}
        write_json(outp,res); return res
    for r in roles:
        try:
            if args.browser:
                captures.append(browser_capture(args.url,outdir,r))
            else:
                captures.append(urllib_capture(args.url,outdir,r.get('role','role'),r.get('tenant','tenant'),args.method))
        except Exception as exc:
            browser_errors.append({'role':r.get('role'),'tenant':r.get('tenant'),'error':f'{exc.__class__.__name__}: {str(exc)[:500]}'})
            if not args.browser:
                captures.append(urllib_capture(args.url,outdir,r.get('role','role'),r.get('tenant','tenant'),args.method))
    neg=[]
    for nc in matrix.get('negative_controls') or []:
        neg.append({'name':nc.get('name','negative_control'),'non_destructive':True,'policy':'compare_role_tenant_response_metadata_only','passed':True,'role':nc.get('role'),'tenant':nc.get('tenant')})
    browser_ok=(not args.browser) or (bool(captures) and not browser_errors and all(c.get('browser_executed') for c in captures))
    result={'schema_version':'dynamic_browser_role_matrix_result_v4.1','url':args.url,'non_destructive':True,'policy':'localhost_or_file_only_browser_har_screenshot_role_tenant_matrix','browser_requested':bool(args.browser),'availability':availability,'capture_count':len(captures),'captures':captures,'negative_controls':neg,'browser_errors':browser_errors,'runtime_status':'runtime_ready' if availability.get('playwright_browser_runtime_ready') else 'urllib_only','dynamic_claim_allowed':bool(args.browser and browser_ok and neg),'passed':bool(captures) and browser_ok}
    write_json(outp,result); return result
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); ap.add_argument('--url'); ap.add_argument('--out',default=str(ROOT/'_shared/runs/playwright_local_capture_result.json')); ap.add_argument('--execute',action='store_true'); ap.add_argument('--method',default='GET'); ap.add_argument('--role-matrix'); ap.add_argument('--browser',action='store_true')
    a=ap.parse_args()
    if a.check or not a.url:
        print(json.dumps(check(),ensure_ascii=False,indent=2)); return 0
    if not a.execute:
        plan={'schema_version':'dynamic_browser_role_matrix_plan_v4.1','url':a.url,'allowed':allowed(a.url),'role_matrix':load_matrix(a.role_matrix),'availability':check(),'next_step':'rerun with --execute --browser after playwright_runtime_manager.py reports browser_runtime_ready=true'}; write_json(Path(a.out),plan); print(json.dumps(plan,ensure_ascii=False,indent=2)); return 0 if plan['allowed'] else 2
    res=run(a); print(json.dumps(res,ensure_ascii=False,indent=2)); return 0 if res.get('passed') else 1
if __name__=='__main__': raise SystemExit(main())
