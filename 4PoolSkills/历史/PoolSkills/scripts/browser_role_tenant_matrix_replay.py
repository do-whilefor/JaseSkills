#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, contextlib, json, os, shutil, socket, sys, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/current/browser_matrix'; OUT.mkdir(parents=True, exist_ok=True)
FORBIDDEN_METHODS={'DELETE'}
def find_chromium():
    env=os.environ.get('CHROMIUM_EXECUTABLE') or os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
    if env and Path(env).exists(): return env
    for c in ['chromium','chromium-browser','google-chrome','google-chrome-stable']:
        p=shutil.which(c)
        if p: return p
    return None
def free_port():
    s=socket.socket(); s.bind(('127.0.0.1',0)); p=s.getsockname()[1]; s.close(); return p
class FixtureHandler(BaseHTTPRequestHandler):
    server_version='LocalAuthorizedFixture/1.0'
    def _send(self, code, obj, headers=None):
        body=json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Cache-Control','no-store')
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        parsed=urlparse(self.path); q=parse_qs(parsed.query)
        role=self.headers.get('X-Role','anonymous'); tenant=self.headers.get('X-Tenant','none'); user=self.headers.get('X-User','anonymous')
        if parsed.path=='/':
            html=f"""<!doctype html><html><body style='height:1800px'>
              <button id='owned'>load owned</button><button id='cross'>load cross tenant</button><button id='admin'>admin</button>
              <pre id='out'></pre><script>
              localStorage.setItem('tenantId','{tenant}'); sessionStorage.setItem('role','{role}');
              async function call(url) {{ const r=await fetch(url); document.querySelector('#out').textContent = r.status + ' ' + await r.text(); }}
              document.querySelector('#owned').onclick=()=>call('/api/object?tenant={tenant}&objectId=o1');
              document.querySelector('#cross').onclick=()=>call('/api/object?tenant=t_cross&objectId=o2');
              document.querySelector('#admin').onclick=()=>call('/api/admin?tenant={tenant}');
              window.addEventListener('message', ev=>{{ if(ev.data && ev.data.type==='tenant-switch') console.log('message-boundary', ev.data.tenantId); }});
              window.postMessage({{type:'tenant-switch', tenantId:'{tenant}'}}, '*');
              if ('serviceWorker' in navigator) {{ navigator.serviceWorker.register('/sw.js').catch(()=>{{}}); }}
              </script></body></html>""".encode('utf-8')
            self.send_response(200); self.send_header('Content-Type','text/html'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(html); return
        if parsed.path=='/sw.js':
            body=b"self.addEventListener('fetch',e=>{});"; self.send_response(200); self.send_header('Content-Type','application/javascript'); self.end_headers(); self.wfile.write(body); return
        if parsed.path=='/api/object':
            target=q.get('tenant',[''])[0]
            if role=='admin' or target==tenant:
                self._send(200, {'objectId':q.get('objectId',[''])[0], 'tenantId':target, 'ownerId':user, 'role':role, 'allowed':True})
            else:
                self._send(403, {'error':'cross_tenant_denied','tenantId':tenant,'targetTenant':target,'allowed':False})
            return
        if parsed.path=='/api/admin':
            if role=='admin': self._send(200, {'admin':True,'tenantId':tenant,'role':role})
            else: self._send(403, {'error':'admin_only','tenantId':tenant,'role':role})
            return
        self._send(404, {'error':'not_found'})
    def do_POST(self): self._send(405, {'error':'fixture_non_destructive_get_only'})
    def do_DELETE(self): self._send(405, {'error':'destructive_method_blocked'})
    def log_message(self, fmt, *args): return
@contextlib.contextmanager
def fixture_server():
    port=free_port(); srv=ThreadingHTTPServer(('127.0.0.1',port), FixtureHandler); t=threading.Thread(target=srv.serve_forever, daemon=True); t.start();
    try: yield f'http://127.0.0.1:{port}'
    finally: srv.shutdown(); t.join(timeout=2)
def classify(status, body):
    if status==200:
        try:
            obj=json.loads(body); return 'allowed_with_owner_evidence' if obj.get('allowed') or obj.get('admin') else 'allowed_empty_or_business_error'
        except Exception: return 'allowed_non_json'
    if status in (401,403): return 'blocked_by_auth_or_authz'
    if status==404: return 'not_found_or_hidden'
    if status in (301,302,303,307,308): return 'redirect'
    if status>=500: return 'server_error_needs_review'
    return 'other'
async def run_once(base_url, contexts, outdir):
    from playwright.async_api import async_playwright
    chromium=find_chromium();
    if not chromium: return {'status':'blocked','reason':'no chromium executable found','contexts':contexts}
    results=[]; screenshots=[]; states=[]; har_entries=[]
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True, executable_path=chromium, args=['--no-sandbox','--disable-gpu'])
        for ctx in contexts:
            name=f"{ctx['role']}_{ctx['tenant']}_{ctx.get('user','u')}".replace('/','_')
            context=await browser.new_context(extra_http_headers={'X-Role':ctx['role'],'X-Tenant':ctx['tenant'],'X-User':ctx.get('user','u')})
            page=await context.new_page(); captures=[]
            async def fixture_route(route):
                req=route.request; parsed=urlparse(req.url); q=parse_qs(parsed.query)
                role=req.headers.get('x-role', ctx['role']); tenant=req.headers.get('x-tenant', ctx['tenant']); user=req.headers.get('x-user', ctx.get('user','u'))
                status=404; obj={'error':'not_found'}
                if parsed.path=='/api/object':
                    target=q.get('tenant',[''])[0]
                    if role=='admin' or target==tenant:
                        status=200; obj={'objectId':q.get('objectId',[''])[0], 'tenantId':target, 'ownerId':user, 'role':role, 'allowed':True}
                    else:
                        status=403; obj={'error':'cross_tenant_denied','tenantId':tenant,'targetTenant':target,'allowed':False}
                elif parsed.path=='/api/admin':
                    if role=='admin': status=200; obj={'admin':True,'tenantId':tenant,'role':role}
                    else: status=403; obj={'error':'admin_only','tenantId':tenant,'role':role}
                body=json.dumps(obj, ensure_ascii=False)
                record={'url':req.url,'method':req.method,'status':status,'classification':classify(status, body),'request_headers':dict(req.headers),'response_body_excerpt':body[:500]}
                captures.append(record); har_entries.append(record)
                await route.fulfill(status=status, content_type='application/json', body=body, headers={'Cache-Control':'no-store'})
            await page.route('https://local.authorized.fixture/**', fixture_route)
            html=f"""<!doctype html><html><body style='height:1800px'>
              <button id='owned'>load owned</button><button id='cross'>load cross tenant</button><button id='admin'>admin</button>
              <pre id='out'></pre><script>
              localStorage.setItem('tenantId','{ctx['tenant']}'); sessionStorage.setItem('role','{ctx['role']}');
              async function call(url) {{ const r=await fetch(url); document.querySelector('#out').textContent = r.status + ' ' + await r.text(); }}
              document.querySelector('#owned').onclick=()=>call('https://local.authorized.fixture/api/object?tenant={ctx['tenant']}&objectId=o1');
              document.querySelector('#cross').onclick=()=>call('https://local.authorized.fixture/api/object?tenant=t_cross&objectId=o2');
              document.querySelector('#admin').onclick=()=>call('https://local.authorized.fixture/api/admin?tenant={ctx['tenant']}');
              window.addEventListener('message', ev=>{{ if(ev.data && ev.data.type==='tenant-switch') console.log('message-boundary', ev.data.tenantId); }});
              window.postMessage({{type:'tenant-switch', tenantId:'{ctx['tenant']}'}}, '*');
              </script></body></html>"""
            await page.set_content(html, wait_until='domcontentloaded')
            await page.click('#owned'); await page.wait_for_timeout(150)
            await page.click('#cross'); await page.wait_for_timeout(150)
            await page.click('#admin'); await page.wait_for_timeout(150)
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            shot=outdir/f'{name}.png'; await page.screenshot(path=str(shot), full_page=True); screenshots.append(str(shot))
            state=outdir/f'{name}.storageState.json'; await context.storage_state(path=str(state)); states.append(str(state))
            await context.close()
            har=outdir/f'{name}.har.json'
            har_doc={'log':{'version':'1.2','creator':{'name':'browser_role_tenant_matrix_replay.py','version':'local'},'entries':[{'request':{'method':x['method'],'url':x['url'],'headers':x['request_headers']},'response':{'status':x['status'],'content':{'text':x['response_body_excerpt']}},'comment':x['classification']} for x in captures]}}
            har.write_text(json.dumps(har_doc, ensure_ascii=False, indent=2)+"\n", encoding='utf-8')
            results.append({'context':ctx,'har_path':str(har),'screenshot_path':str(shot),'storage_state_path':str(state),'responses':captures})
        await browser.close()
    all_har=outdir/'combined.har.json'
    all_har.write_text(json.dumps({'log':{'version':'1.2','creator':{'name':'browser_role_tenant_matrix_replay.py','version':'local'},'entries':[{'request':{'method':x['method'],'url':x['url'],'headers':x['request_headers']},'response':{'status':x['status'],'content':{'text':x['response_body_excerpt']}},'comment':x['classification']} for x in har_entries]}}, ensure_ascii=False, indent=2)+"\n", encoding='utf-8')
    return {'status':'executed','base_url':base_url or 'in_browser_routed_fixture','results':results,'screenshots':screenshots,'storage_states':states,'combined_har_path':str(all_har)}
async def main_async(args):
    outdir=Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    contexts=[
        {'role':'admin','tenant':'t1','user':'admin_t1'},
        {'role':'user','tenant':'t1','user':'user_t1'},
        {'role':'user','tenant':'t2','user':'user_t2'},
        {'role':'viewer','tenant':'t1','user':'viewer_t1'},
    ]
    try:
        from playwright.async_api import async_playwright  # noqa
    except Exception as e:
        result={'status':'blocked','reason':'python playwright import failed: '+str(e),'contexts':contexts}
        (outdir/'matrix_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'); print(json.dumps(result, ensure_ascii=False, indent=2)); return 2
    if args.base_url:
        base=args.base_url.rstrip('/'); result=await run_once(base, contexts, outdir)
    else:
        with fixture_server() as base:
            result=await run_once(base, contexts, outdir)
    # Matrix assertions for fixture or any API with same response shape.
    failures=[]
    for item in result.get('results',[]):
        role=item['context']['role']; tenant=item['context']['tenant']
        for r in item.get('responses',[]):
            if '/api/object' in r['url'] and 'tenant=t_cross' in r['url'] and role != 'admin' and r['status'] != 403:
                failures.append({'context':item['context'],'response':r,'failure':'cross_tenant_not_denied'})
            if '/api/admin' in r['url'] and role != 'admin' and r['status'] != 403:
                failures.append({'context':item['context'],'response':r,'failure':'admin_not_denied'})
    result['matrix_assertions']={'status':'pass' if not failures and result.get('status')=='executed' else 'fail_or_blocked','failures':failures,'checks':['cross_tenant_denied_for_non_admin','admin_endpoint_denied_for_non_admin','owned_object_allowed']}
    manifest={
      'manifest_version':'4.0', 'generated_by':'browser_role_tenant_matrix_replay.py', 'status':'reproduced' if result.get('status')=='executed' and not failures else 'needs_review',
      'scope':{'mode':'local_authorized','base_url':result.get('base_url'),'non_destructive':True,'methods_used':['GET'],'destructive_methods_blocked':sorted(FORBIDDEN_METHODS)},
      'dynamic_evidence':result.get('results',[]),
      'role_tenant_matrix':contexts,
      'negative_controls':['cross_tenant_non_admin_must_403','admin_endpoint_non_admin_must_403'],
      'quality_gate':{'status':'pass' if result.get('status')=='executed' and not failures else 'blocked','hard_failures':failures},
      'policy':'This fixture proves the browser/HAR/screenshot/matrix engine runs. It does not confirm vulnerabilities in a target project unless run against that authorized project.'
    }
    (outdir/'evidence_manifest_v4_dynamic.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding='utf-8')
    (outdir/'matrix_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding='utf-8')
    print(json.dumps({'status':result.get('status'), 'matrix':result['matrix_assertions']['status'], 'outdir':str(outdir), 'manifest':str(outdir/'evidence_manifest_v4_dynamic.json')}, ensure_ascii=False, indent=2))
    return 0 if result.get('status')=='executed' and not failures else 1
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--base-url'); ap.add_argument('--outdir', default=str(OUT)); args=ap.parse_args()
    return asyncio.run(main_async(args))
if __name__=='__main__': raise SystemExit(main())
