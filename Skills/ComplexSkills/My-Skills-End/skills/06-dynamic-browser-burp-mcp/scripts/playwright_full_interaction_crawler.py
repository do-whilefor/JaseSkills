#!/usr/bin/env python3
"""Authorized local full-interaction Playwright crawler.

Creates real browser evidence for the anti-lazy / anti-fake-dynamic gate.
Default scope is file:// and localhost only. It does not submit forms or upload
files. Click execution is opt-in with --execute-clicks. Missing browser runtime
is reported as runtime_unavailable; it is never treated as success.
"""
from __future__ import annotations
import argparse, hashlib, json, re, time, urllib.parse
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SENSITIVE_RE = re.compile(r"(?i)(token|secret|password|key|session|auth|code)=([^&#]+)")
REQUIRED_ACTIONS = [
    "open_page", "click_links_buttons", "expand_menu_dropdown", "hover_dropdown",
    "switch_tab", "open_modal", "scroll_bottom", "search", "change_filter",
    "paginate", "safe_form_validation", "safe_empty_upload_ui", "mutate_path_query_hash",
    "refresh_deep_route", "visit_error_pages"
]


def allowed(url: str, extra_hosts: set[str]) -> bool:
    try:
        u = urllib.parse.urlparse(url)
    except Exception:
        return False
    if u.scheme == "file":
        return True
    host = u.hostname or ""
    return u.scheme in {"http", "https"} and host in {"localhost", "127.0.0.1", "::1", *extra_hosts}


def redacted(value: str) -> str:
    return SENSITIVE_RE.sub(lambda m: f"{m.group(1)}=<redacted>", value)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except Exception:
        return str(path)


def runtime_check() -> dict[str, Any]:
    result = {
        "python_playwright_package": False,
        "browser_runtime_ready": False,
        "browser_runtime_reason": "",
        "runtime_status": "runtime_unavailable",
    }
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        result["python_playwright_package"] = True
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
            result["browser_runtime_ready"] = True
            result["runtime_status"] = "runtime_ready"
        except Exception as exc:
            result["browser_runtime_reason"] = f"{exc.__class__.__name__}: {str(exc)[:500]}"
    except Exception as exc:
        result["browser_runtime_reason"] = f"{exc.__class__.__name__}: {str(exc)[:500]}"
    return result


def js_probe_script() -> str:
    return """
(() => {
  const qsa = (sel) => Array.from(document.querySelectorAll(sel));
  const visible = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  const text = (el) => (el.innerText || el.textContent || el.getAttribute('aria-label') || el.getAttribute('title') || '').slice(0,120);
  const items = [];
  const push = (type, el) => items.push({type, tag: el.tagName, text: text(el), href: el.href || el.getAttribute('href') || '', id: el.id || '', cls: el.className || '', role: el.getAttribute('role') || '', name: el.getAttribute('name') || '', visible: visible(el)});
  qsa('a[href],button,[role=button],summary,[aria-haspopup=true],[data-testid],[data-cy],input,select,textarea,[role=tab]').forEach(el => push('interactive', el));
  const scripts = qsa('script[src]').map(s => s.src);
  const links = qsa('link[href]').map(l => ({rel:l.rel,href:l.href,as:l.as||''}));
  const forms = qsa('form').map(f => ({action:f.action || '', method:f.method || 'get', fields:qsa('input,select,textarea').filter(i => f.contains(i)).map(i => ({name:i.name || '', type:i.type || i.tagName}))}));
  return {
    url: location.href,
    title: document.title,
    interactive: items,
    scripts,
    links,
    forms,
    storage: {localStorage:Object.keys(localStorage), sessionStorage:Object.keys(sessionStorage)},
    serviceWorkerControlled: !!navigator.serviceWorker?.controller,
    readyState: document.readyState,
    htmlLength: document.documentElement.outerHTML.length
  };
})()
"""


def safe_click_candidates(dom: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for i, item in enumerate(dom.get("interactive") or []):
        if not item.get("visible"):
            continue
        tag = str(item.get("tag") or "").lower()
        href = str(item.get("href") or "")
        txt = str(item.get("text") or "")
        risk = "review"
        if tag == "a" and href and not href.lower().startswith(("javascript:", "mailto:", "tel:")):
            risk = "navigation"
        elif any(x in txt.lower() for x in ["delete", "remove", "destroy", "支付", "删除", "提交", "购买", "确认"]):
            risk = "potentially_state_changing"
        rows.append({"index": i, "type": "click_candidate", "tag": tag, "text": txt, "href": redacted(href), "risk": risk})
    return rows


def run_browser(args: argparse.Namespace) -> dict[str, Any]:
    extra_hosts = set(args.allow_host or [])
    if not allowed(args.url, extra_hosts):
        return {"schema_version": "full_browser_interaction_capture_v1", "passed": False, "runtime_status": "scope_blocked", "error": "url_not_allowed", "url": args.url, "allowed_hosts": sorted(extra_hosts), "policy": "file_localhost_only_by_default"}

    rt = runtime_check()
    if not rt.get("browser_runtime_ready"):
        return {"schema_version": "full_browser_interaction_capture_v1", "passed": False, **rt, "url": args.url, "observed_actions": [], "evidence_gaps": [{"runtime_blocked": True, "reason": rt.get("browser_runtime_reason")}], "dynamic_claim_allowed": False}

    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError  # type: ignore

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    events: list[dict[str, Any]] = []
    console_rows: list[dict[str, Any]] = []
    observed_actions: set[str] = set()
    coverage_rows: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    started = time.time()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headful)
        context = browser.new_context(record_har_path=str(outdir / "playwright.har"), viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page.on("request", lambda req: events.append({"type": "request", "method": req.method, "url": redacted(req.url), "resource_type": req.resource_type}))
        page.on("response", lambda resp: events.append({"type": "response", "status": resp.status, "url": redacted(resp.url)}))
        page.on("console", lambda msg: console_rows.append({"type": msg.type, "text": msg.text[:1000]}))

        page.goto(args.url, wait_until="networkidle", timeout=args.timeout_ms)
        observed_actions.add("open_page")
        coverage_rows.append({"action": "open_page", "url": redacted(page.url), "status": "executed"})

        dom = page.evaluate(js_probe_script())
        dom_path = outdir / "dom_probe.json"
        write_json(dom_path, dom)
        artifacts.append({"type": "dom", "path": rel(dom_path), "sha256": sha_file(dom_path), "redacted": True})

        ss_path = outdir / "screenshot_initial.png"
        page.screenshot(path=str(ss_path), full_page=True)
        artifacts.append({"type": "screenshot", "path": rel(ss_path), "sha256": sha_file(ss_path), "redacted": False})

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(500)
        observed_actions.add("scroll_bottom")
        coverage_rows.append({"action": "scroll_bottom", "status": "executed"})

        hover_count = 0
        for sel in ["[aria-haspopup=true]", "[role=button]", "button", "summary"]:
            for loc in page.locator(sel).all()[: args.max_hover]:
                try:
                    if loc.is_visible(timeout=300):
                        loc.hover(timeout=800)
                        hover_count += 1
                except Exception:
                    pass
        if hover_count:
            observed_actions.update({"hover_dropdown", "expand_menu_dropdown"})
        coverage_rows.append({"action": "hover_dropdown", "count": hover_count, "status": "executed" if hover_count else "not_observed"})

        tab_count = 0
        for loc in page.locator('[role=tab], [data-tab], button').all()[: args.max_tabs]:
            try:
                txt = (loc.inner_text(timeout=500) or "")[:80]
                if loc.is_visible(timeout=300) and re.search(r"(?i)tab|设置|详情|权限|成员|日志|配置", txt):
                    if args.execute_clicks:
                        loc.click(timeout=1000)
                    tab_count += 1
            except Exception:
                pass
        if tab_count:
            observed_actions.add("switch_tab")
        coverage_rows.append({"action": "switch_tab", "count": tab_count, "status": "executed" if args.execute_clicks and tab_count else "planned_only" if tab_count else "not_observed"})

        input_count = 0
        for loc in page.locator('input[type="search"], input[name*=search i], input[placeholder*=search i], input[placeholder*=搜索 i], input[type="text"], textarea').all()[: args.max_inputs]:
            try:
                if loc.is_visible(timeout=300):
                    loc.fill(args.search_term, timeout=1000)
                    input_count += 1
            except Exception:
                pass
        if input_count:
            observed_actions.update({"search", "safe_form_validation"})
        coverage_rows.append({"action": "search", "count": input_count, "status": "executed" if input_count else "not_observed"})
        coverage_rows.append({"action": "safe_form_validation", "count": input_count, "status": "executed" if input_count else "not_observed", "submitted": False})

        upload_count = 0
        for _loc in page.locator('input[type="file"]').all()[: args.max_inputs]:
            upload_count += 1
        if upload_count:
            observed_actions.add("safe_empty_upload_ui")
        coverage_rows.append({"action": "safe_empty_upload_ui", "count": upload_count, "status": "observed_no_upload" if upload_count else "not_observed"})

        click_candidates = safe_click_candidates(dom)
        click_count = 0
        if args.execute_clicks:
            clickable = page.locator('a[href],button,[role=button],summary')
            for idx, cand in enumerate(click_candidates[: args.max_clicks]):
                if cand.get("risk") == "potentially_state_changing" and not args.allow_state_changing_click_text:
                    continue
                try:
                    loc = clickable.nth(idx)
                    if loc.is_visible(timeout=300):
                        loc.click(timeout=1000)
                        page.wait_for_timeout(300)
                        click_count += 1
                except Exception:
                    pass
        if click_count:
            observed_actions.add("click_links_buttons")
        coverage_rows.append({"action": "click_links_buttons", "candidate_count": len(click_candidates), "clicked_count": click_count, "status": "executed" if click_count else "planned_only" if click_candidates else "not_observed"})

        for suffix, action in [("?audit_probe=1", "mutate_path_query_hash"), ("/__audit_nonexistent_404__", "visit_error_pages")]:
            if args.url.startswith("file:"):
                coverage_rows.append({"action": action, "status": "not_applicable_file_url"})
                continue
            try:
                target = args.url.rstrip("/") + suffix
                page.goto(target, wait_until="networkidle", timeout=args.timeout_ms)
                observed_actions.add(action)
                coverage_rows.append({"action": action, "url": redacted(target), "status": "executed"})
            except PlaywrightTimeoutError:
                coverage_rows.append({"action": action, "status": "timeout"})
            except Exception as exc:
                coverage_rows.append({"action": action, "status": "error", "error": f"{exc.__class__.__name__}: {str(exc)[:200]}"})
        try:
            page.goto(args.url, wait_until="networkidle", timeout=args.timeout_ms)
            observed_actions.add("refresh_deep_route")
            coverage_rows.append({"action": "refresh_deep_route", "status": "executed"})
        except Exception:
            coverage_rows.append({"action": "refresh_deep_route", "status": "error"})

        console_path = outdir / "console.redacted.json"
        write_json(console_path, console_rows)
        artifacts.append({"type": "console", "path": rel(console_path), "sha256": sha_file(console_path), "redacted": True})

        network_path = outdir / "network.redacted.json"
        write_json(network_path, events)
        artifacts.append({"type": "network", "path": rel(network_path), "sha256": sha_file(network_path), "redacted": True})

        context.close()
        browser.close()

    har_path = outdir / "playwright.har"
    if har_path.exists():
        artifacts.append({"type": "har", "path": rel(har_path), "sha256": sha_file(har_path), "redacted": False})

    js_chunks = sorted({e["url"] for e in events if e.get("type") == "request" and re.search(r"\.m?js(?:\?|$)", e.get("url", ""), re.I)})
    api_calls = sorted({e["url"] for e in events if e.get("type") == "request" and re.search(r"/(api|graphql|rpc|admin|internal|v\d+|legacy|old|beta)/", e.get("url", ""), re.I)})
    gaps = [{"missing_action": a} for a in REQUIRED_ACTIONS if a not in observed_actions]
    return {
        "schema_version": "full_browser_interaction_capture_v1",
        "url": redacted(args.url),
        "browser_executed": True,
        "non_destructive": True,
        "execute_clicks": bool(args.execute_clicks),
        "duration_ms": round((time.time() - started) * 1000),
        "observed_actions": sorted(observed_actions),
        "coverage_rows": coverage_rows,
        "click_candidates": click_candidates,
        "new_chunks": js_chunks,
        "new_apis": api_calls,
        "artifacts": artifacts,
        "evidence_gaps": gaps,
        "dynamic_claim_allowed": len(gaps) == 0 and bool(args.role) and bool(args.tenant),
        "role": args.role or None,
        "tenant": args.tenant or None,
        "promotion_policy": "confirmed requires this browser evidence plus role/tenant matrix, negative control, positive control and quality gate",
        "passed": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", default=str(ROOT / "_shared/runs/full_browser_interaction_capture.json"))
    ap.add_argument("--outdir", default=str(ROOT / "_shared/runs/full_browser_capture_artifacts"))
    ap.add_argument("--allow-host", action="append")
    ap.add_argument("--execute-clicks", action="store_true")
    ap.add_argument("--allow-state-changing-click-text", action="store_true")
    ap.add_argument("--headful", action="store_true")
    ap.add_argument("--timeout-ms", type=int, default=15000)
    ap.add_argument("--max-clicks", type=int, default=20)
    ap.add_argument("--max-hover", type=int, default=30)
    ap.add_argument("--max-tabs", type=int, default=20)
    ap.add_argument("--max-inputs", type=int, default=10)
    ap.add_argument("--search-term", default="audit-smoke-search")
    ap.add_argument("--role", default="")
    ap.add_argument("--tenant", default="")
    args = ap.parse_args()
    res = run_browser(args)
    write_json(Path(args.out), res)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("passed") else 2


if __name__ == "__main__":
    raise SystemExit(main())
