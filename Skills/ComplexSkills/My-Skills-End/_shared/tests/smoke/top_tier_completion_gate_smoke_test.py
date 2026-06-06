#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def run(cmd):
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)


def main() -> int:
    tmp = Path(tempfile.mkdtemp())
    surface = tmp / "surface.json"
    cands = tmp / "candidates.json"
    lazy = tmp / "lazy.json"
    browser = tmp / "browser.json"
    matrix = tmp / "matrix.json"
    variants = tmp / "variants.json"
    surface.write_text(json.dumps({"routes":[{"route":"/api/projects/{id}/export","method":"GET","file":"app/routes.py","line":10,"guard":"tenant policy"},{"route":"/api/projects/{id}/download","method":"GET","file":"app/routes.py","line":20}]}, ensure_ascii=False), encoding="utf-8")
    cands.write_text(json.dumps({"candidates":[{"candidate_id":"CAND-1","template_id":"C03","route":"/api/projects/{id}/export","file":"app/routes.py","line":10}]}, ensure_ascii=False), encoding="utf-8")
    lazy.write_text(json.dumps({"files_scanned": 3, "browser_trigger_required": 1, "browser_trigger_status":"planned_only"}, ensure_ascii=False), encoding="utf-8")
    browser.write_text(json.dumps({"runtime_status":"planned_only","observed_actions":[],"browser_executed":False,"dynamic_claim_allowed":False}, ensure_ascii=False), encoding="utf-8")

    role_script = ROOT / "skills/06-dynamic-browser-burp-mcp/scripts/role_tenant_authz_matrix_builder.py"
    var_script = ROOT / "skills/07-vulnerability-hunting-engine/scripts/variant_expansion_engine.py"
    guard = ROOT / "_shared/quality/final_claim_guard.py"

    cp = run([sys.executable, str(role_script), "--surface", str(surface), "--candidates", str(cands), "--out", str(matrix)])
    assert cp.returncode == 0, cp.stderr
    mat = json.loads(matrix.read_text(encoding="utf-8"))
    assert mat["test_case_count"] > 0

    cp = run([sys.executable, str(var_script), "--candidates", str(cands), "--surface", str(surface), "--lazy-js", str(lazy), "--out", str(variants)])
    assert cp.returncode == 0, cp.stderr
    var = json.loads(variants.read_text(encoding="utf-8"))
    assert var["candidate_count"] > 0 and var["expansions"]

    cp = run([sys.executable, str(guard), "--claim-level", "confirmed", "--browser-coverage", str(browser), "--lazy-js-ledger", str(lazy), "--role-tenant-matrix", str(matrix), "--variant-expansion", str(variants)])
    assert cp.returncode == 1, "guard must block unsupported confirmed claim"
    obj = json.loads(cp.stdout)
    assert obj["allowed"] is False
    assert obj["blockers"], obj
    print(json.dumps({"passed": True, "blocked_confirmed_claim": True, "blockers": obj["blockers"][:5]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
