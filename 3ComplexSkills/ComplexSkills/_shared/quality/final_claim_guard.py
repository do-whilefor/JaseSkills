#!/usr/bin/env python3
"""Final claim guard: block unsupported confirmed/dynamic-complete claims."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def load(path: str | None) -> Any:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return {"_missing": str(p)}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception as exc:
        return {"_load_error": f"{exc.__class__.__name__}: {exc}", "path": str(p)}


def has_browser_coverage(obj: Any) -> tuple[bool, list[str]]:
    errs: list[str] = []
    if not isinstance(obj, dict):
        return False, ["browser_coverage_missing"]
    if obj.get("runtime_status") in {"runtime_missing", "planned_only", "runtime_unavailable", "scope_blocked"} or obj.get("browser_executed") is False:
        errs.append("browser_runtime_not_executed")
    actions = set(obj.get("observed_actions") or [])
    for action in ["open_page", "scroll_bottom"]:
        if action not in actions:
            errs.append(f"missing_browser_action:{action}")
    if not (obj.get("new_chunks") or obj.get("new_apis") or obj.get("coverage_rows")):
        errs.append("browser_no_runtime_assets_or_rows")
    artifacts = obj.get("artifacts") or obj.get("evidence_files") or []
    if not artifacts:
        errs.append("browser_artifacts_missing")
    return not errs, errs


def has_lazy_ledger(obj: Any) -> tuple[bool, list[str]]:
    errs: list[str] = []
    if not isinstance(obj, dict):
        return False, ["lazy_js_ledger_missing"]
    if obj.get("files_scanned", 0) <= 0:
        errs.append("lazy_js_no_files_scanned")
    if obj.get("browser_trigger_required", 0) > 0 and obj.get("browser_trigger_status") not in {"executed", "not_applicable_with_evidence"}:
        errs.append("lazy_js_browser_trigger_unresolved")
    return not errs, errs



def has_manifest_index(obj: Any) -> tuple[bool, list[str]]:
    errs: list[str] = []
    if not isinstance(obj, dict):
        return False, ["manifest_index_missing"]
    if obj.get("schema_version") != "manifest_index_v1" or obj.get("source_policy") != "explicit_manifest_index_only":
        errs.append("manifest_index_schema_or_source_policy_invalid")
    for i, item in enumerate(obj.get("manifests") or []):
        if item.get("fixture_allowed") is True:
            errs.append(f"manifest_index[{i}] fixture_allowed_true_blocks_confirmed_dashboard")
    return not errs, errs

def has_role_tenant_matrix(obj: Any) -> tuple[bool, list[str]]:
    errs: list[str] = []
    if not isinstance(obj, dict):
        return False, ["role_tenant_matrix_missing"]
    if not obj.get("roles"):
        errs.append("roles_missing")
    if not obj.get("tenants"):
        errs.append("tenants_missing")
    if obj.get("test_case_count", 0) <= 0:
        errs.append("role_tenant_test_cases_missing")
    if obj.get("status") == "planned_only_until_executed":
        errs.append("role_tenant_matrix_not_executed")
    return not errs, errs


def has_variant_expansion(obj: Any) -> tuple[bool, list[str]]:
    errs: list[str] = []
    if not isinstance(obj, dict):
        return False, ["variant_expansion_missing"]
    if obj.get("candidate_count", 0) > 0 and not obj.get("expansions"):
        errs.append("variant_expansion_empty")
    unresolved = 0
    for exp in obj.get("expansions") or []:
        for variant in exp.get("variants") or []:
            if str(variant.get("status", "")).endswith("needs_execution"):
                unresolved += 1
    if unresolved:
        errs.append(f"variant_expansion_unexecuted:{unresolved}")
    return not errs, errs


def run_quality_gate(manifest: str | None) -> tuple[bool, list[str], Any]:
    if not manifest:
        return False, ["evidence_manifest_missing"], None
    qg = ROOT / "_shared/quality/quality_gate_v4_1.py"
    if not qg.exists():
        return False, ["quality_gate_missing"], None
    cp = subprocess.run([sys.executable, str(qg), str(manifest)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    try:
        obj = json.loads(cp.stdout)
    except Exception:
        return False, ["quality_gate_non_json", cp.stderr[:300]], None
    return bool(obj.get("passed")), obj.get("errors") or obj.get("blocking_reasons") or [], obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--claim-level", choices=["candidate", "likely", "confirmed", "dynamic_complete", "full_frontend_coverage"], default="candidate")
    ap.add_argument("--manifest")
    ap.add_argument("--browser-coverage")
    ap.add_argument("--lazy-js-ledger")
    ap.add_argument("--role-tenant-matrix")
    ap.add_argument("--variant-expansion")
    ap.add_argument("--manifest-index")
    ap.add_argument("--out")
    args = ap.parse_args()

    browser_ok, browser_errs = has_browser_coverage(load(args.browser_coverage))
    lazy_ok, lazy_errs = has_lazy_ledger(load(args.lazy_js_ledger))
    matrix_ok, matrix_errs = has_role_tenant_matrix(load(args.role_tenant_matrix))
    variant_ok, variant_errs = has_variant_expansion(load(args.variant_expansion))
    manifest_index_ok, manifest_index_errs = has_manifest_index(load(args.manifest_index))
    qg_ok, qg_errs, qg_obj = run_quality_gate(args.manifest)

    blockers: list[str] = []
    if args.claim_level in {"dynamic_complete", "full_frontend_coverage", "confirmed"} and not browser_ok:
        blockers.extend(browser_errs)
    if args.claim_level in {"full_frontend_coverage", "confirmed"} and not lazy_ok:
        blockers.extend(lazy_errs)
    if args.claim_level == "confirmed" and not qg_ok:
        blockers.extend(qg_errs or ["quality_gate_not_passed"])
    if args.claim_level == "confirmed" and not matrix_ok:
        blockers.extend(matrix_errs)
    if args.claim_level == "confirmed" and not variant_ok:
        blockers.extend(variant_errs)
    if args.claim_level == "confirmed" and not manifest_index_ok:
        blockers.extend(manifest_index_errs)

    result = {
        "schema_version": "final_claim_guard_v2",
        "claim_level": args.claim_level,
        "allowed": not blockers,
        "blockers": blockers,
        "component_status": {
            "browser_coverage_ok": browser_ok,
            "lazy_js_ledger_ok": lazy_ok,
            "role_tenant_matrix_ok": matrix_ok,
            "variant_expansion_ok": variant_ok,
            "quality_gate_ok": qg_ok,
            "manifest_index_ok": manifest_index_ok,
        },
        "quality_gate_result": qg_obj,
        "policy": "no confirmed/dynamic-complete/full-frontend-coverage claim without executed evidence and gates",
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if result["allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
