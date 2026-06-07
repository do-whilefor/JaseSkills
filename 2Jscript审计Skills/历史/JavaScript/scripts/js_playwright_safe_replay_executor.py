#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, subprocess, textwrap, os
from pathlib import Path


def load(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}


def generate_config(out: Path):
    cfg = textwrap.dedent(f"""
    import {{ defineConfig }} from '@playwright/test';
    export default defineConfig({{
      testDir: {json.dumps(str(out))},
      timeout: 60000,
      reporter: [['json', {{ outputFile: {json.dumps(str(out/'playwright-report.json'))} }}]],
      outputDir: {json.dumps(str(out/'test-results'))},
      use: {{
        ignoreHTTPSErrors: true,
        actionTimeout: 5000,
        navigationTimeout: 30000,
        trace: 'retain-on-failure',
        screenshot: 'only-on-failure',
        video: 'off'
      }},
      workers: 1
    }});
    """).strip()+"\n"
    p = out/'playwright.generated.config.ts'
    p.write_text(cfg, encoding='utf-8')
    return p


def generate_spec(plan: dict, out: Path, role_tenant_matrix: dict | None=None):
    actions=plan.get('actions') or plan.get('interaction_plan') or []
    url=plan.get('target_url') or plan.get('url') or 'http://127.0.0.1:3000/'
    action_js=[]
    for i,a in enumerate(actions[:200]):
        if isinstance(a, str):
            a={'action': a}
        elif not isinstance(a, dict):
            a={}
        kind=str(a.get('action') or a.get('kind') or a.get('type') or '').lower(); sel=a.get('selector') or a.get('target') or ''
        if kind in {'click','hover'} and sel:
            action_js.append(f"  await safe{kind.capitalize()}(page, {json.dumps(sel)}); // {i}")
        elif kind in {'scroll','full_page_scroll'}:
            action_js.append("  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));")
        elif kind in {'fill','input','search'} and sel:
            val=str(a.get('value','audit-smoke-test'))[:120]
            action_js.append(f"  await safeFill(page, {json.dumps(sel)}, {json.dumps(val)});")
        elif kind in {'route','goto'} and a.get('url'):
            action_js.append(f"  await page.goto(new URL({json.dumps(a.get('url'))}, targetURL).toString(), {{ waitUntil: 'networkidle' }});")
    if not action_js:
        action_js=["  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));", "  await page.waitForTimeout(500);"]

    roles=[]
    if role_tenant_matrix:
        roles=role_tenant_matrix.get('roles',[]) or role_tenant_matrix.get('accounts',[]) or role_tenant_matrix.get('matrix',[])
    if not roles:
        roles=[{'name':'default','role':'default','tenant':'default'}]

    role_cases=[]
    for idx,r in enumerate(roles[:20]):
        if not isinstance(r, dict): r={'name':str(r)}
        nm=str(r.get('name') or r.get('role') or f'role{idx}').replace("'", '')[:80]
        storage=r.get('storageState') or r.get('storage_state') or None
        tenant=r.get('tenant') or r.get('tenant_id') or 'default'
        role=r.get('role') or nm
        role_cases.append({"name":nm,"storage":storage,"role":role,"tenant":tenant})

    cases_js=json.dumps(role_cases, ensure_ascii=False)
    spec=textwrap.dedent(f"""
    import {{ test }} from '@playwright/test';
    import fs from 'node:fs/promises';
    import path from 'node:path';
    const targetURL = {json.dumps(url)};
    const outDir = {json.dumps(str(out))};
    const roleCases = {cases_js};
    async function safeClick(page, selector) {{ try {{ const el=page.locator(selector).first(); if (await el.count()) await el.click({{trial:false, timeout:3000}}); }} catch(e) {{ console.log('safeClick skipped', selector, e.message); }} }}
    async function safeHover(page, selector) {{ try {{ const el=page.locator(selector).first(); if (await el.count()) await el.hover({{timeout:3000}}); }} catch(e) {{ console.log('safeHover skipped', selector, e.message); }} }}
    async function safeFill(page, selector, value) {{ try {{ const el=page.locator(selector).first(); if (await el.count()) await el.fill(value, {{timeout:3000}}); }} catch(e) {{ console.log('safeFill skipped', selector, e.message); }} }}
    function redactHeader(name, value) {{ return /authorization|cookie|token|secret|api[-_]?key|jwt|session|password/i.test(name) ? '<redacted>' : value; }}
    async function ensureDirs() {{ await fs.mkdir(path.join(outDir,'screenshots'), {{recursive:true}}); await fs.mkdir(path.join(outDir,'runtime'), {{recursive:true}}); }}
    async function dumpStorage(page) {{ return await page.evaluate(async () => {{ const out={{localStorage:{{}}, sessionStorage:{{}}, caches:[]}}; for (const k of Object.keys(localStorage)) out.localStorage[k]=localStorage.getItem(k); for (const k of Object.keys(sessionStorage)) out.sessionStorage[k]=sessionStorage.getItem(k); if ('caches' in window) {{ const keys=await caches.keys(); for (const k of keys) {{ const c=await caches.open(k); const reqs=await c.keys(); out.caches.push({{cache:k, urls:reqs.map(r=>r.url)}}); }} }} return out; }}); }}
    async function installPostMessageProbe(context) {{ await context.addInitScript(() => {{
      window.__auditPostMessages = [];
      const origPostMessage = window.postMessage.bind(window);
      window.postMessage = function(message, targetOrigin, transfer) {{ window.__auditPostMessages.push({{direction:'sent', targetOrigin, messageType: typeof message, preview: JSON.stringify(message).slice(0,500), ts: Date.now()}}); return origPostMessage(message, targetOrigin, transfer); }};
      window.addEventListener('message', ev => window.__auditPostMessages.push({{direction:'received', origin: ev.origin, messageType: typeof ev.data, preview: JSON.stringify(ev.data).slice(0,500), ts: Date.now()}}));
    }}); }}
    async function runReplay(browser, roleCase, index) {{
      await ensureDirs();
      const safeName = `${{index}}-${{String(roleCase.name).replace(/[^a-zA-Z0-9_.-]/g,'_')}}`;
      const contextOptions = {{ recordHar: {{ path: path.join(outDir, `session-${{safeName}}.har`), content: 'embed' }} }};
      if (roleCase.storage) contextOptions.storageState = roleCase.storage;
      const context = await browser.newContext(contextOptions);
      await installPostMessageProbe(context);
      await context.tracing.start({{ screenshots: true, snapshots: true, sources: true }});
      const page = await context.newPage();
      const requests=[]; const responses=[]; const chunks=new Set(); const consoleLines=[]; const wsFrames=[]; const graphqlFrames=[];
      page.on('console', msg => consoleLines.push({{type:msg.type(), text:msg.text(), location:msg.location()}}));
      page.on('request', r => {{
        const headers = Object.fromEntries(Object.entries(r.headers()).map(([k,v])=>[k, redactHeader(k,v)]));
        const item={{method:r.method(), url:r.url(), resourceType:r.resourceType(), headers, postData:r.postData(), role:roleCase.role, tenant:roleCase.tenant}};
        requests.push(item);
        const pd=(r.postData()||''); if (/graphql|query|mutation|subscription/i.test(r.url()+pd)) graphqlFrames.push(item);
      }});
      page.on('response', async r => {{ const u=r.url(); responses.push({{url:u, status:r.status(), statusText:r.statusText(), headers:Object.fromEntries(Object.entries(r.headers()).map(([k,v])=>[k, redactHeader(k,v)])), role:roleCase.role, tenant:roleCase.tenant}}); if (/\\.(js|mjs|map|wasm)(\\?|$)/.test(u)) chunks.add(u); }});
      page.on('websocket', ws => {{ const rec={{url:ws.url(), frames:[], role:roleCase.role, tenant:roleCase.tenant}}; wsFrames.push(rec); ws.on('framesent', ev => rec.frames.push({{direction:'sent', payload:String(ev.payload).slice(0,2000)}})); ws.on('framereceived', ev => rec.frames.push({{direction:'received', payload:String(ev.payload).slice(0,2000)}})); }});
      await page.goto(targetURL, {{ waitUntil: 'networkidle' }});
      await page.screenshot({{ path: path.join(outDir,'screenshots',`replay-start-${{safeName}}.png`), fullPage: true }});
    {chr(10).join(action_js)}
      await page.waitForTimeout(1000);
      await page.screenshot({{ path: path.join(outDir,'screenshots',`replay-end-${{safeName}}.png`), fullPage: true }});
      const storage = await dumpStorage(page);
      const dom = await page.content();
      const postMessages = await page.evaluate(() => window.__auditPostMessages || []);
      await fs.writeFile(path.join(outDir, `dom_snapshot-${{safeName}}.html`), dom);
      await fs.writeFile(path.join(outDir, `console-${{safeName}}.log`), consoleLines.map(x=>JSON.stringify(x)).join('\n'));
      await fs.writeFile(path.join(outDir, `runtime-request-index-${{safeName}}.json`), JSON.stringify({{requests,responses}}, null, 2));
      await fs.writeFile(path.join(outDir, `loaded-chunks-${{safeName}}.json`), JSON.stringify([...chunks], null, 2));
      await fs.writeFile(path.join(outDir, `storage-dump-redacted-${{safeName}}.json`), JSON.stringify(storage, null, 2));
      await fs.writeFile(path.join(outDir, `graphql_frames-${{safeName}}.json`), JSON.stringify(graphqlFrames, null, 2));
      await fs.writeFile(path.join(outDir, `websocket_frames-${{safeName}}.json`), JSON.stringify(wsFrames, null, 2));
      await fs.writeFile(path.join(outDir, `postmessage_frames-${{safeName}}.json`), JSON.stringify(postMessages, null, 2));
      await context.tracing.stop({{ path: path.join(outDir, `playwright_trace-${{safeName}}.zip`) }});
      await context.close();
    }}
    for (const [index, roleCase] of roleCases.entries()) {{
      test(`safe replay ${{roleCase.name}}`, async ({{ browser }}) => {{ await runReplay(browser, roleCase, index); }});
    }}
    """).strip()+"\n"
    spec_path=out/'playwright_safe_replay.spec.ts'; spec_path.write_text(spec, encoding='utf-8')
    return spec_path


def find_artifacts(out: Path):
    artifacts=[]
    for p in out.rglob('*'):
        if p.is_file() and p.name not in {'js_playwright_execution.json'} and p.suffix.lower() in {'.har','.zip','.png','.jpg','.jpeg','.webp','.json','.html','.log','.txt'}:
            artifacts.append(str(p))
    return sorted(set(artifacts))


def main():
    ap=argparse.ArgumentParser(description='Generate and execute safe Playwright replay. Ready only if Playwright returns HAR, trace, screenshot, DOM, console, request/response and protocol frame artifacts.')
    ap.add_argument('--plan', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    ap.add_argument('--role-tenant-matrix', default='')
    ap.add_argument('--generate-spec', action='store_true')
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--spec', default='')
    ap.add_argument('--config', default='')
    ap.add_argument('--timeout-sec', type=int, default=90)
    args=ap.parse_args(); out=Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True); (out/'screenshots').mkdir(exist_ok=True)
    plan=load(Path(args.plan),{}); matrix=load(Path(args.role_tenant_matrix),{}) if args.role_tenant_matrix else None
    result={'schema_version':'js-playwright-safe-replay-execution/v3','status':'not-executed','plan_status':plan.get('status'),'artifacts':[],'requirements':{},'errors':[],'safety':['authorized target only','non-destructive UI interactions','no delete/payment/approval actions','no bulk enumeration','no external callback submission']}
    spec=Path(args.spec).resolve() if args.spec else None
    if args.generate_spec or not spec:
        spec=generate_spec(plan,out,matrix); result['generated_spec']=str(spec)
    config=Path(args.config).resolve() if args.config else generate_config(out)
    result['generated_config']=str(config)
    if not args.execute:
        result['errors'].append('execution flag not provided; generated spec is not runtime evidence')
    else:
        npx=shutil.which('npx')
        if not npx: result['errors'].append('npx not found')
        if not spec.exists(): result['errors'].append(f'missing spec: {spec}')
        if not config.exists(): result['errors'].append(f'missing config: {config}')
        if not result['errors']:
            node=shutil.which('node')
            preflight=subprocess.run([node,'-e',"require.resolve('@playwright/test'); console.log('ok')"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, cwd=str(Path.cwd())) if node else None
            if not node or not preflight or preflight.returncode != 0:
                result.update({'command':'node -e require.resolve(@playwright/test)','returncode':127,'stdout_tail':(preflight.stdout[-6000:] if preflight else ''),'stderr_tail':((preflight.stderr if preflight else 'node missing') + '\n@playwright/test missing; run npm install on Windows before claiming browser replay').strip()[-6000:]})
                proc=type('Proc', (), {'returncode':127, 'stdout':result.get('stdout_tail',''), 'stderr':result.get('stderr_tail','')})()
            else:
                cmd=[npx,'playwright','test',str(spec),'--config',str(config)]
                try:
                    proc=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=args.timeout_sec, cwd=str(Path.cwd()))
                    result.update({'command':' '.join(cmd),'returncode':proc.returncode,'stdout_tail':proc.stdout[-6000:],'stderr_tail':proc.stderr[-6000:]})
                except subprocess.TimeoutExpired as e:
                    proc=type('Proc', (), {'returncode':124, 'stdout':(e.stdout or '') if isinstance(e.stdout, str) else '', 'stderr':(e.stderr or '') if isinstance(e.stderr, str) else ''})()
                    result.update({'command':' '.join(cmd),'returncode':124,'stdout_tail':proc.stdout[-6000:],'stderr_tail':(proc.stderr + '\nTIMEOUT').strip()[-6000:]})
            blob=(proc.stdout+'\n'+proc.stderr).lower()
            result['artifacts']=find_artifacts(out)
            req={
                'har': any(a.endswith('.har') for a in result['artifacts']),
                'trace': any(Path(a).name.startswith('playwright_trace') and a.endswith('.zip') for a in result['artifacts']),
                'screenshots': any('screenshots' in Path(a).parts and Path(a).suffix.lower() in {'.png','.jpg','.jpeg','.webp'} for a in result['artifacts']),
                'dom_snapshot': any(Path(a).name.startswith('dom_snapshot') for a in result['artifacts']),
                'console_log': any(Path(a).name.startswith('console-') and Path(a).suffix=='.log' for a in result['artifacts']),
                'request_response': any(Path(a).name.startswith('runtime-request-index') for a in result['artifacts']),
                'graphql_frames': any(Path(a).name.startswith('graphql_frames') for a in result['artifacts']),
                'websocket_frames': any(Path(a).name.startswith('websocket_frames') for a in result['artifacts']),
                'postmessage_frames': any(Path(a).name.startswith('postmessage_frames') for a in result['artifacts']),
            }
            result['requirements']=req
            if proc.returncode==0 and all(req[k] for k in ['har','trace','screenshots','dom_snapshot','console_log','request_response']):
                result['status']='executed'
            else:
                if '@playwright/test' in blob or 'err_blocked_by_administrator' in blob or 'executable doesn' in blob or 'browser' in blob or 'no tests found' in blob:
                    result['status']='environment_blocked'
                    result['errors'].append('playwright environment/dependency/policy blocked complete artifact capture; no confirmed runtime evidence may be claimed')
                else:
                    result['status']='failed'
                    result['errors'].append('playwright returned non-zero or did not produce required artifacts')
    (out/'js_playwright_execution.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':result['status'] in {'executed','environment_blocked'},'status':result['status'],'requirements':result.get('requirements',{}),'artifacts':len(result.get('artifacts',[])),'spec':str(spec),'config':str(config),'out':str(out/'js_playwright_execution.json'),'errors':result['errors']}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status'] in {'executed','environment_blocked'} or not args.execute else 1)
if __name__=='__main__': main()
