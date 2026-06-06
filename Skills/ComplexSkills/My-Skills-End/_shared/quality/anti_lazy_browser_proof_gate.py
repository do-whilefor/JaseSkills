#!/usr/bin/env python3
"""Anti-lazy/browser proof gate.

Validates that JS lazy asset discovery and browser interaction evidence support
any claim of complete frontend coverage or dynamic validation. It is intentionally
strict: missing evidence blocks promotion instead of lowering standards.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from typing import Any

REQUIRED_LEDGER_KEYS = ['static_js_assets','dynamic_imports','source_maps','service_workers','build_manifests','api_clients','browser_trigger_required','evidence_gaps']
CRITICAL_BROWSER_ACTIONS = {'open_page','click_links_buttons','scroll_bottom','safe_form_validation'}
AUTHZ_TEMPLATES = {'C02-authz-bypass','C03-idor-bola','C04-tenant-isolation-bypass','C05-admin-privilege-escalation','C17-graphql-access-control','C19-jwt-token-validation','C20-oauth-sso-callback-redirect','C21-cors-high-risk'}

def load(path: str | None) -> Any:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return {'_missing_path': path}
    try:
        return json.loads(p.read_text(encoding='utf-8', errors='ignore'))
    except Exception as exc:
        return {'_parse_error': f'{exc.__class__.__name__}: {exc}', '_path': path}

def evaluate(ledger: Any, matrix: Any, claim: dict[str, Any] | None = None) -> dict[str, Any]:
    claim = claim or {}
    blocked=[]; warnings=[]; gaps=[]
    if not isinstance(ledger, dict) or ledger.get('_missing_path') or ledger.get('_parse_error'):
        blocked.append('missing_or_invalid_lazy_js_asset_ledger')
    else:
        if ledger.get('schema_version') != 'lazy_js_asset_ledger_v1':
            blocked.append('lazy_ledger_schema_version_mismatch')
        for key in REQUIRED_LEDGER_KEYS:
            if key not in ledger:
                blocked.append(f'lazy_ledger_missing_{key}')
        if ledger.get('files_scanned', 0) <= 0:
            blocked.append('lazy_ledger_scanned_no_files')
        # Empty findings are allowed only when the gap is explicitly recorded.
        for key in ['dynamic_imports','source_maps','service_workers','build_manifests','api_clients']:
            if not ledger.get(key):
                gaps.append({'missing_or_absent': key, 'must_be_explained': True})
    if not isinstance(matrix, dict) or matrix.get('_missing_path') or matrix.get('_parse_error'):
        blocked.append('missing_or_invalid_browser_interaction_matrix')
    else:
        if matrix.get('schema_version') != 'browser_interaction_coverage_v1':
            blocked.append('browser_matrix_schema_version_mismatch')
        runtime_status = matrix.get('runtime_status')
        if runtime_status in {'runtime_missing','planned_only'} and claim.get('claims_dynamic_validation_complete'):
            blocked.append('dynamic_validation_claimed_but_browser_runtime_missing')
        observed=set(matrix.get('observed_actions') or [])
        missing_actions=sorted(CRITICAL_BROWSER_ACTIONS - observed)
        if missing_actions and claim.get('claims_frontend_coverage_complete'):
            blocked.append('frontend_coverage_claimed_without_critical_interactions:' + ','.join(missing_actions))
        if claim.get('template_id') in AUTHZ_TEMPLATES and not matrix.get('role_tenant_matrix_present'):
            blocked.append('authz_related_claim_without_role_tenant_matrix')
        if matrix.get('dynamic_claim_allowed') is not True and claim.get('desired_final_status') == 'confirmed':
            blocked.append('confirmed_requested_without_browser_dynamic_claim_allowed')
    if claim.get('desired_final_status') == 'confirmed' and claim.get('has_negative_control') is not True:
        blocked.append('confirmed_requested_without_negative_control')
    if claim.get('desired_final_status') == 'confirmed' and claim.get('has_evidence_manifest') is not True:
        blocked.append('confirmed_requested_without_evidence_manifest')
    passed = not blocked
    promotion = 'allowed_to_quality_gate' if passed else 'blocked_to_candidate_or_needs_review'
    return {
        'schema_version': 'anti_lazy_browser_proof_gate_v1',
        'passed': passed,
        'blocked_reasons': blocked,
        'warnings': warnings,
        'evidence_gaps': gaps,
        'promotion_policy': promotion,
        'claim_checked': claim,
        'rule': 'no lazy-JS completion or dynamic-validation claim without concrete ledger, browser matrix, role/tenant evidence and negative control when applicable'
    }

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--lazy-ledger')
    ap.add_argument('--browser-matrix')
    ap.add_argument('--claim-json')
    ap.add_argument('--out')
    args=ap.parse_args()
    result=evaluate(load(args.lazy_ledger), load(args.browser_matrix), load(args.claim_json) if args.claim_json else {})
    text=json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text+'\n', encoding='utf-8')
    print(text)
    return 0 if result.get('passed') else 1

if __name__ == '__main__':
    raise SystemExit(main())
