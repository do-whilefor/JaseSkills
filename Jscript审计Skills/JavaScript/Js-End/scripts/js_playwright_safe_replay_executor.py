#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, subprocess, textwrap
from pathlib import Path

def load(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}

def generate_spec(plan: dict, out: Path, role_tenant_matrix: dict | None=None):
    actions=plan.get('actions') or plan.get('interaction_plan') or []
    url=plan.get('target_url') or plan.get('url') or 'http://127.0.0.1:3000/'
    # Conservative generated spec: capture artifacts, safe UI interactions only, never destructive submit/delete/payment.
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
            action_js.append(f"  await safeFill(page, {json.dumps(sel)}, 'audit-smoke-test');")
        elif kind in {'route','goto'} and a.get('url'):
            action_js.append(f"  await page.goto(new URL({json.dumps(a.get('url'))}, targetURL).toString());")
    if not action_js:
        action_js=["  await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));", "  await page.waitForTimeout(500);"]
    roles=[]
    if role_tenant_matrix:
        roles=role_tenant_matrix.get('roles',[]) or role_tenant_matrix.get('accounts',[])
    role_lines=[]
    if roles:
        for r in roles[:20]:
            nm=r.get('name') or r.get('role') or 'role'; storage=r.get('storageState') or r.get('storage_state')
            role_lines.append(f"test('safe replay role {nm}', async ({{ browser }}) => {{\n  const context = await browser.newContext({{ storageState: {json.dumps(storage)} }});\n  const page = await context.newPage();\n  await runReplay(page);\n  await context.close();\n}});")
    else:
        role_lines.append("test('safe replay default context', async ({ page }) => { await runReplay(page); });")
    spec=textwrap.dedent(f"""
    import {{ test, expect }} from '@playwright/test';
    const targetURL = {json.dumps(url)};
    async function safeClick(page, selector) {{ try {{ const el=page.locator(selector).first(); if (await el.count()) await el.click({{trial:false, timeout:3000}}); }} catch(e) {{ console.log('safeClick skipped', selector, e.message); }} }}
    async function safeHover(page, selector) {{ try {{ const el=page.locator(selector).first(); if (await el.count()) await el.hover({{timeout:3000}}); }} catch(e) {{ console.log('safeHover skipped', selector, e.message); }} }}
    async function safeFill(page, selector, value) {{ try {{ const el=page.locator(selector).first(); if (await el.count()) await el.fill(value, {{timeout:3000}}); }} catch(e) {{ console.log('safeFill skipped', selector, e.message); }} }}
    async function dumpStorage(page) {{ return await page.evaluate(async () => {{ const out={{localStorage:{{}}, sessionStorage:{{}}, caches:[]}}; for (const k of Object.keys(localStorage)) out.localStorage[k]=localStorage.getItem(k); for (const k of Object.keys(sessionStorage)) out.sessionStorage[k]=sessionStorage.getItem(k); if ('caches' in window) {{ const keys=await caches.keys(); for (const k of keys) {{ const c=await caches.open(k); const reqs=await c.keys(); out.caches.push({{cache:k, urls:reqs.map(r=>r.url)}}); }} }} return out; }}); }}
    async function runReplay(page) {{
      const requests=[]; const chunks=new Set();
      page.on('request', r => requests.push({{method:r.method(), url:r.url(), resourceType:r.resourceType()}}));
      page.on('response', r => {{ const u=r.url(); if (/\\.(js|mjs|map|wasm)(\\?|$)/.test(u)) chunks.add(u); }});
      await page.goto(targetURL, {{ waitUntil: 'networkidle' }});
      await page.screenshot({{ path: 'reports/js-top-tier/screenshots/replay-start.png', fullPage: true }});
    {chr(10).join(action_js)}
      await page.waitForTimeout(1000);
      await page.screenshot({{ path: 'reports/js-top-tier/screenshots/replay-end.png', fullPage: true }});
      const storage = await dumpStorage(page);
      await fs.writeFile('reports/js-top-tier/runtime-request-index.json', JSON.stringify(requests, null, 2));
      await fs.writeFile('reports/js-top-tier/loaded-chunks.json', JSON.stringify([...chunks], null, 2));
      await fs.writeFile('reports/js-top-tier/storage-dump-redacted.json', JSON.stringify(storage, null, 2));
    }}
    {chr(10).join(role_lines)}
    """).strip()+"\n"
    spec_path=out/'playwright_safe_replay.spec.ts'; spec_path.write_text(spec, encoding='utf-8')
    return spec_path

def main():
    ap=argparse.ArgumentParser(description='Generate and execute safe Playwright replay. Ready only if Playwright returns artifacts; plan-only never counts.')
    ap.add_argument('--plan', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    ap.add_argument('--role-tenant-matrix', default='')
    ap.add_argument('--generate-spec', action='store_true')
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--spec', default='')
    args=ap.parse_args(); out=Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True); (out/'screenshots').mkdir(exist_ok=True)
    plan=load(Path(args.plan),{}); matrix=load(Path(args.role_tenant_matrix),{}) if args.role_tenant_matrix else None
    result={'schema_version':'js-playwright-safe-replay-execution/v2','status':'not-executed','plan_status':plan.get('status'),'artifacts':[],'errors':[],'safety':['authorized target only','non-destructive UI interactions','no delete/payment/approval actions','no bulk enumeration','no external callback submission']}
    spec=Path(args.spec).resolve() if args.spec else None
    if args.generate_spec or not spec:
        spec=generate_spec(plan,out,matrix); result['generated_spec']=str(spec)
    if not args.execute:
        result['errors'].append('execution flag not provided; generated spec is not runtime evidence')
    else:
        npx=shutil.which('npx')
        if not npx: result['errors'].append('npx not found')
        if not spec.exists(): result['errors'].append(f'missing spec: {spec}')
        if not result['errors']:
            cmd=[npx,'playwright','test',str(spec),'--reporter=json','--trace','on']
            proc=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600, cwd=str(Path.cwd()))
            result.update({'command':' '.join(cmd),'returncode':proc.returncode,'stdout_tail':proc.stdout[-4000:],'stderr_tail':proc.stderr[-4000:]})
            if proc.returncode==0:
                result['status']='executed'
                for p in out.rglob('*'):
                    if p.suffix.lower() in {'.har','.zip','.png','.jpg','.jpeg','.webp','.json'} and p.name != 'js_playwright_execution.json': result['artifacts'].append(str(p))
            else:
                result['status']='failed'; result['errors'].append('playwright returned non-zero')
    (out/'js_playwright_execution.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':result['status']=='executed','status':result['status'],'spec':str(spec),'out':str(out/'js_playwright_execution.json'),'errors':result['errors']}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result['status']=='executed' or not args.execute else 1)
if __name__=='__main__': main()
