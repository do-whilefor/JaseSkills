#!/usr/bin/env python3
"""Playwright multi-role storageState executor for local/authorized targets.

Defaults to plan-only unless --execute is supplied and the URL is localhost/file/data.
Browser runtime is marked ready only after a real Chromium launch succeeds.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, urllib.parse
from pathlib import Path
from typing import Any


def load(p: str | None) -> dict[str, Any]:
    return json.loads(Path(p).read_text(encoding='utf-8', errors='ignore')) if p and Path(p).exists() else {}


def is_local_url(url: str | None) -> bool:
    if not url:
        return False
    try:
        u = urllib.parse.urlparse(url)
    except Exception:
        return False
    if u.scheme in {'file', 'data'}:
        return True
    return u.scheme in {'http', 'https'} and (u.hostname or '').lower() in {'localhost', '127.0.0.1', '::1'}


def join_url(base: str, route: str) -> str:
    if route.startswith(('http://', 'https://', 'file:', 'data:')):
        return route
    if not route.startswith('/'):
        route = '/' + route
    return urllib.parse.urljoin(base.rstrip('/') + '/', route.lstrip('/'))


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8', errors='ignore')).hexdigest()


def runtime_ready() -> tuple[bool, Any, str]:
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception as exc:
        return False, None, f'{exc.__class__.__name__}: {exc}'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True, sync_playwright, ''
    except Exception as exc:
        return False, sync_playwright, f'{exc.__class__.__name__}: {str(exc)[:500]}'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--matrix')
    ap.add_argument('--storage-state', action='append', default=[])
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--base-url')
    ap.add_argument('--out')
    a = ap.parse_args()
    matrix = load(a.matrix)
    rows: list[dict[str, Any]] = []
    ready, sp, reason = runtime_ready()
    executed = False
    blockers: list[str] = []
    cases = (matrix.get('test_cases') or [])[:50]
    if a.execute and not ready:
        blockers.append('playwright_browser_not_ready:' + reason)
    if a.execute and not a.base_url:
        blockers.append('base_url_required')
    if a.execute and a.base_url and not is_local_url(a.base_url):
        blockers.append('base_url_not_local_or_explicitly_safe')
    if a.execute and not blockers:
        executed = True
        with sp() as p:
            browser = p.chromium.launch(headless=True)
            for i, c in enumerate(cases):
                storage = a.storage_state[i % len(a.storage_state)] if a.storage_state else None
                ctx = browser.new_context(storage_state=storage)
                page = ctx.new_page(); status = None; title = ''; err = ''
                route = str(c.get('route') or '/')
                target = join_url(a.base_url, route)
                try:
                    resp = page.goto(target, wait_until='domcontentloaded', timeout=10000)
                    status = resp.status if resp else None
                    title = page.title()
                except Exception as exc:
                    err = str(exc)[:300]
                rows.append({'case_id': 'PWROLE-' + str(i + 1), 'role': c.get('replay_role'), 'tenant': c.get('replay_tenant'), 'route': route, 'url': target, 'status': status, 'title_sha256': stable_hash(title), 'error': err, 'non_destructive': True, 'artifacts': [], 'redacted': True})
                ctx.close()
            browser.close()
    else:
        for i, c in enumerate(cases):
            rows.append({'case_id': 'PWROLE-' + str(i + 1), 'planned': True, 'role': c.get('replay_role'), 'tenant': c.get('replay_tenant'), 'route': c.get('route'), 'non_destructive': True})
    res = {'schema_version': 'playwright_multirole_replay_v1', 'executor': 'playwright_multirole_replay.py', 'executed': executed, 'runtime_ready': ready, 'runtime_reason': reason, 'blockers': blockers, 'rows': rows, 'promotion_policy': 'Only executed=true rows with request/response artifacts may contribute to confirmed dynamic evidence; planned rows cannot.'}
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text + '\n', encoding='utf-8')
    else:
        print(text)
    return 0 if not (a.execute and blockers) else 1


if __name__ == '__main__':
    raise SystemExit(main())
