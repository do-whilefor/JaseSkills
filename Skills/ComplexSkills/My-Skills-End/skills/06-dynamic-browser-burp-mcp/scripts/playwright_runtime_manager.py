#!/usr/bin/env python3
"""Playwright browser runtime installer/probe v4.3.

The script never marks browser runtime as ready unless a real browser launch succeeds.
`--install` runs the local Python Playwright installer, which may require internet.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path

def probe() -> dict:
    res = {"schema_version":"playwright_runtime_readiness_v4.3","python_package":False,"browser_runtime_ready":False,"browser_launch_verified":False,"install_command":"python -m playwright install chromium","policy":"ready only after chromium launch succeeds","errors":[]}
    try:
        import playwright.sync_api  # type: ignore
        res["python_package"] = True
    except Exception as exc:
        res["errors"].append(f"python package missing: {exc.__class__.__name__}: {exc}")
        return res
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            page = b.new_page()
            page.goto('data:text/html,<title>probe</title>')
            title = page.title()
            b.close()
        res["browser_runtime_ready"] = True
        res["browser_launch_verified"] = (title == 'probe')
    except Exception as exc:
        res["errors"].append(f"browser launch failed: {exc.__class__.__name__}: {str(exc)[:500]}")
    return res

def install() -> dict:
    cmd = [sys.executable, '-m', 'playwright', 'install', 'chromium']
    try:
        cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=300)
        return {"schema_version":"playwright_runtime_install_v4.3","command":cmd,"returncode":cp.returncode,"stdout_tail":cp.stdout[-2000:],"stderr_tail":cp.stderr[-2000:],"post_probe":probe()}
    except Exception as exc:
        return {"schema_version":"playwright_runtime_install_v4.3","command":cmd,"error":f"{exc.__class__.__name__}: {exc}","post_probe":probe()}

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--install', action='store_true'); ap.add_argument('--out')
    args = ap.parse_args(); res = install() if args.install else probe(); text=json.dumps(res, ensure_ascii=False, indent=2)
    if args.out: Path(args.out).parent.mkdir(parents=True, exist_ok=True); Path(args.out).write_text(text+'\n', encoding='utf-8')
    print(text); return 0 if (res.get('browser_runtime_ready') or not args.install) else 1
if __name__ == '__main__': raise SystemExit(main())
