#!/usr/bin/env python3
"""Attack surface ledger builder v2.

Merges project_inventory_v2, code graph, JS audit and dynamic evidence into a
non-confirming Route/API/Worker/GraphQL/RPC/Webhook/File-flow ledger. Read-only.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from typing import Any

def load(path: str | None) -> Any:
    if not path: return {}
    p = Path(path)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}

def sha16(x: str) -> str: return hashlib.sha256(x.encode()).hexdigest()[:16]
def as_list(x: Any) -> list: return x if isinstance(x, list) else []

def add_surface(out: dict[str, Any], typ: str, source: str, route: str='', method: str='', path: str='', evidence: Any=None, risk_hint: str='review'):
    item = {'surface_id': 'SURF-' + sha16('|'.join([typ,source,route,method,path,json.dumps(evidence,ensure_ascii=False)[:200]])), 'type': typ, 'source': source, 'route': route, 'method': method, 'path': path, 'risk_hint': risk_hint, 'evidence': evidence, 'confirmation_policy':'surface_only_not_vulnerability'}
    out['attack_surface'].append(item)
    out.setdefault(typ + '_surface', []).append(item)


def build_role_object_tenant_ledger(inventory: dict[str, Any], code: dict[str, Any], js: dict[str, Any]) -> dict[str, Any]:
    ledger={'schema_version':'role_object_tenant_ledger_v1','role_signals':[],'object_id_signals':[],'tenant_signals':[],'owner_check_signals':[],'route_boundary_matrix':[],'high_risk_unresolved_routes':[],'confirmation_policy':'ledger maps IDOR/tenant obligations only; it cannot confirm vulnerabilities'}
    def blob(x): return json.dumps(x, ensure_ascii=False).lower()
    object_rx=['id','user_id','account_id','invoice_id','order_id','project_id','file_id','resource_id']
    role_rx=['role','permission','admin','rbac','abac','acl','policy','guard']
    tenant_rx=['tenant','org_id','workspace','organization','team_id','company_id']
    for src_name, rows in [('inventory_authz', inventory.get('authz_policy_guard',[])),('code_authz', code.get('authz_boundaries',[])),('js_permissions', js.get('frontend_permissions',[]))]:
        for x in as_list(rows):
            b=blob(x)
            if any(t in b for t in role_rx): ledger['role_signals'].append({'source':src_name,'item':x})
            if 'owner' in b or 'user_id' in b: ledger['owner_check_signals'].append({'source':src_name,'item':x})
    for src_name, rows in [('inventory_tenant', inventory.get('tenant_model_signals',[])),('code_tenant', code.get('tenant_boundaries',[])),('js_i18n', js.get('i18n_keys',[]))]:
        for x in as_list(rows):
            if any(t in blob(x) for t in tenant_rx): ledger['tenant_signals'].append({'source':src_name,'item':x})
    routes=as_list(inventory.get('routes'))+as_list(code.get('routes'))+as_list(js.get('api_clients'))
    guards=as_list(code.get('authz_boundaries'))+as_list(code.get('middleware_boundaries'))+as_list(inventory.get('authz_policy_guard'))
    tenants=as_list(code.get('tenant_boundaries'))+as_list(inventory.get('tenant_model_signals'))
    for r in routes:
        rb=blob(r); obj=any(t in rb for t in object_rx) or '{id}' in rb or '/:' in rb
        same_file_guards=[g for g in guards if isinstance(g,dict) and (g.get('file') and (g.get('file')==r.get('file') or g.get('file')==r.get('path')) or g.get('path') and g.get('path')==r.get('path'))]
        same_file_tenants=[t for t in tenants if isinstance(t,dict) and (t.get('file') and (t.get('file')==r.get('file') or t.get('file')==r.get('path')) or t.get('path') and t.get('path')==r.get('path'))]
        row={'route':r.get('route') or r.get('target') or r.get('path',''),'method':r.get('method','UNKNOWN'),'file':r.get('file') or r.get('path',''),'has_object_reference':obj,'guard_signal_count':len(same_file_guards),'tenant_signal_count':len(same_file_tenants),'status':'mapped'}
        ledger['route_boundary_matrix'].append(row)
        if obj and (len(same_file_guards)==0 or len(same_file_tenants)==0): ledger['high_risk_unresolved_routes'].append({**row,'reason':'object route lacks same-file guard or tenant signal; requires dynamic role/tenant matrix'})
    return ledger


def build(inventory: dict[str, Any], code: dict[str, Any], js: dict[str, Any], dynamic: dict[str, Any] | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {'schema_version':'attack_surface_ledger_v2','non_destructive':True,'attack_surface':[], 'coverage_obligations':[], 'route_to_candidate_inputs':[]}
    for r in as_list(inventory.get('routes')) + as_list(code.get('routes')):
        add_surface(out, 'http_route', 'inventory_or_code_graph', r.get('route') or r.get('path',''), r.get('method','UNKNOWN'), r.get('path') or r.get('file',''), r, 'authz_review')
    for a in as_list(js.get('api_clients')):
        target = a.get('target') or a.get('url','')
        add_surface(out, 'frontend_api', 'js_audit', target, a.get('method','UNKNOWN'), a.get('file',''), a, 'frontend_backend_mapping_review')
    for g in as_list(js.get('graphql')) + as_list(inventory.get('api_schema_files')):
        blob = json.dumps(g, ensure_ascii=False).lower()
        if 'graphql' in blob:
            add_surface(out, 'graphql', 'schema_or_js', '/graphql', 'POST', g.get('path') or g.get('file',''), g, 'resolver_auth_review')
        if 'proto' in blob or 'grpc' in blob:
            add_surface(out, 'grpc', 'schema_or_inventory', '', 'RPC', g.get('path',''), g, 'rpc_auth_review')
        if 'rpc' in blob and 'grpc' not in blob:
            add_surface(out, 'rpc', 'schema_or_inventory', '', 'RPC', g.get('path',''), g, 'rpc_auth_review')
    for x in as_list(inventory.get('worker_queue_cron_cli_rpc_webhook')):
        blob = json.dumps(x, ensure_ascii=False).lower()
        typ = 'webhook' if 'webhook' in blob else 'cron' if 'cron' in blob or 'schedule' in blob else 'queue_worker' if any(k in blob for k in ['queue','worker','consumer','job']) else 'cli_rpc'
        add_surface(out, typ, 'inventory', '', 'ASYNC', x.get('path',''), x, 'non_http_boundary_review')
    for x in as_list(inventory.get('high_risk_file_flows')):
        add_surface(out, 'file_flow', 'inventory', '', 'LOCAL_OR_HTTP', x.get('path',''), x, 'file_read_write_upload_preview_review')
    for x in as_list(inventory.get('auth_signals')) + as_list(inventory.get('authz_policy_guard')):
        add_surface(out, 'auth_boundary', 'inventory', '', '', x.get('path',''), x, 'auth_authz_boundary_review')
    for x in as_list(inventory.get('tenant_model_signals')):
        add_surface(out, 'tenant_boundary', 'inventory', '', '', x.get('path',''), x, 'tenant_isolation_review')
    for x in as_list(inventory.get('admin_debug_fallback')):
        add_surface(out, 'admin_debug_fallback', 'inventory', '', '', x.get('path',''), x, 'admin_debug_fallback_review')
    for x in as_list(inventory.get('feature_flags')) + as_list(js.get('feature_flags')):
        add_surface(out, 'feature_flag_hidden_function', 'inventory_or_js', '', '', x.get('path') or x.get('file',''), x, 'hidden_surface_review')
    for x in as_list(inventory.get('i18n_messages')) + as_list(js.get('i18n_keys')):
        add_surface(out, 'i18n_hidden_module_hint', 'inventory_or_js', '', '', x.get('path') or x.get('file',''), x, 'hidden_module_review')
    for x in as_list(inventory.get('storybook_mock_e2e_flows')):
        add_surface(out, 'test_mock_storybook_flow', 'inventory', '', '', x.get('path',''), x, 'business_flow_extraction_review')
    out['role_object_tenant_ledger'] = build_role_object_tenant_ledger(inventory, code, js)
    out['surface_count'] = len(out['attack_surface'])
    for s in out['attack_surface']:
        out['route_to_candidate_inputs'].append({'surface_id': s['surface_id'], 'type': s['type'], 'route': s.get('route'), 'path': s.get('path'), 'candidate_engine_input': True})
    out['coverage_obligations'] = [
        'HTTP routes must map auth/authz/tenant boundaries before confirmed',
        'worker/queue/cron/CLI/RPC/webhook surfaces must not be dropped from candidate generation',
        'file-flow surfaces require false-positive filters for test/mock/dead code',
        'JS-discovered APIs must be reconciled with backend routes or marked unresolved',
        'feature flag/i18n/analytics/test-flow hints are candidate inputs only',
        'role-object-tenant ledger must be completed for IDOR and tenant-isolation candidates before confirmation'
    ]
    return out

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--inventory'); ap.add_argument('--code-graph'); ap.add_argument('--js-audit'); ap.add_argument('--dynamic'); ap.add_argument('--out')
    args = ap.parse_args(); res = build(load(args.inventory), load(args.code_graph), load(args.js_audit), load(args.dynamic)); text=json.dumps(res,ensure_ascii=False,indent=2)
    if args.out: Path(args.out).parent.mkdir(parents=True, exist_ok=True); Path(args.out).write_text(text+'\n',encoding='utf-8')
    else: print(text)
    return 0
if __name__ == '__main__': raise SystemExit(main())
