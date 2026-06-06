#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]

def load_mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

def main() -> int:
    lazy = load_mod(ROOT/'skills/05-js-audit-runtime/scripts/lazy_js_asset_discovery.py', 'lazy_js_asset_discovery')
    matrix_mod = load_mod(ROOT/'skills/06-dynamic-browser-burp-mcp/scripts/browser_interaction_coverage_matrix.py', 'browser_interaction_coverage_matrix')
    gate = load_mod(ROOT/'_shared/quality/anti_lazy_browser_proof_gate.py', 'anti_lazy_browser_proof_gate')
    with tempfile.TemporaryDirectory() as td:
        d=Path(td); (d/'src').mkdir()
        (d/'src/app.js').write_text("const Admin=React.lazy(()=>import('./Admin')); fetch('/api/admin/users'); new WebSocket('/ws/audit');", encoding='utf-8')
        (d/'src/app.js.map').write_text('{"version":3,"sourcesContent":["fetch(\'/api/hidden\')"]}', encoding='utf-8')
        (d/'public').mkdir(); (d/'public/sw.js').write_text('self.addEventListener("install",()=>caches.open("v1"));', encoding='utf-8')
        ledger = lazy.discover(d)
        assert ledger['schema_version'] == 'lazy_js_asset_ledger_v1'
        assert ledger['dynamic_imports'] and ledger['api_clients'] and ledger['service_workers']
        import argparse
        matrix = matrix_mod.build(argparse.Namespace(har=None, capture_json=None, action=['open_page','click_links_buttons','scroll_bottom','safe_form_validation','switch_role','switch_tenant'], role=['user','admin'], tenant=['tenantA','tenantB'], page='http://localhost/', planned_only=False, runtime_reason='smoke'))
        result = gate.evaluate(ledger, matrix, {'claims_frontend_coverage_complete': True, 'claims_dynamic_validation_complete': False, 'desired_final_status': 'candidate', 'template_id': 'C03-idor-bola'})
        assert result['passed'] is True, result
    print(json.dumps({'schema_version':'anti_lazy_browser_gate_smoke_test_v1','passed':True}, ensure_ascii=False, indent=2))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
