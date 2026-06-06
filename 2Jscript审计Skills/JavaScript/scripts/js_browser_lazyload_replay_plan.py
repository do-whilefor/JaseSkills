#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def parse_roles(p:str):
    if not p: return [{'role':'anonymous','storage_state':None,'tenant':'none'}]
    data=json.loads(Path(p).read_text(encoding='utf-8'))
    if isinstance(data, list): return data
    return data.get('roles', [{'role':'anonymous','storage_state':None,'tenant':'none'}])

def main():
    ap=argparse.ArgumentParser(description='Generate safe Playwright lazyload/browser interaction replay plan')
    ap.add_argument('--url', action='append', default=[], help='authorized seed URL; may be repeated')
    ap.add_argument('--roles-json', default='', help='optional roles/tenants storageState matrix json')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    urls=args.url or ['http://127.0.0.1:3000/']
    roles=parse_roles(args.roles_json)
    actions=['goto','wait_network_idle','full_page_scroll','click_visible_links_and_buttons_limited','hover_menus','switch_tabs','open_dialogs','spa_route_back_forward','search_input_safe_probe','desktop_viewport','mobile_viewport','locale_switch_if_available','collect_local_session_indexeddb_cache_keys','save_har_trace_screenshot']
    forbidden=['delete','payment_submit','approval_submit','bulk_export','bulk_import','external_callback_send','destructive_update','large_enumeration']
    plan={'schema_version':'js-browser-replay-plan/v1','status':'plan-only','authorization_required':True,'seed_urls':urls,'role_tenant_matrix':roles,'actions':actions,'forbidden_actions':forbidden,'evidence_outputs':['HAR','Playwright trace','screenshots','console log','network request/response metadata','loaded chunk list','service worker/cache inventory'],'downgrade':'plan-only until executed in authorized local/test environment'}
    (out/'js_browser_replay_plan.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
    spec = """import { test, expect } from '@playwright/test';
const seedUrls = __URLS__;
const forbiddenText = /(delete|remove|pay|approve|submit payment|bulk export|bulk import|send webhook)/i;
async function safeExplore(page) {
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await page.screenshot({ path: `reports/js-top-tier/screenshots/${Date.now()}-initial.png`, fullPage: true }).catch(() => {});
  for (let i = 0; i < 8; i++) await page.mouse.wheel(0, 900).catch(() => {});
  const locators = [page.getByRole('button'), page.getByRole('link'), page.locator('[role="tab"]'), page.locator('[aria-haspopup="menu"]')];
  for (const loc of locators) {
    const count = Math.min(await loc.count().catch(() => 0), 25);
    for (let i = 0; i < count; i++) {
      const item = loc.nth(i);
      const text = await item.innerText({ timeout: 1000 }).catch(() => '');
      if (forbiddenText.test(text)) continue;
      await item.hover({ timeout: 1000 }).catch(() => {});
      await item.click({ timeout: 1500 }).catch(() => {});
      await page.waitForLoadState('networkidle', { timeout: 5000 }).catch(() => {});
    }
  }
  await page.goBack({ timeout: 3000 }).catch(() => {});
  await page.goForward({ timeout: 3000 }).catch(() => {});
}
test('authorized safe lazyload/chunk exploration', async ({ page, context }) => {
  await context.tracing.start({ screenshots: true, snapshots: true });
  for (const url of seedUrls) {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await safeExplore(page);
  }
  await context.tracing.stop({ path: 'reports/js-top-tier/playwright-trace.zip' });
});
""".replace('__URLS__', json.dumps(urls, ensure_ascii=False))
    (out/'playwright_safe_replay.spec.ts').write_text(spec, encoding='utf-8')
    print(json.dumps({'ok':True,'plan':str(out/'js_browser_replay_plan.json'),'spec':str(out/'playwright_safe_replay.spec.ts'),'status':'plan-only'}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()
