#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import sys
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
from _info_collect_lib import now_iso, stable_hash, find_unredacted_secrets  # type: ignore


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8', errors='ignore'))


def manifest_items(data: dict) -> list[dict]:
    return [x for x in data.get('items', []) if isinstance(x, dict)]


def finding(status: str, title: str, category: str, evs: list[str], confidence: float, reason: str, limitation: str, extra: dict | None = None) -> dict:
    obj={
        'id': 'find-' + stable_hash(title + category + ''.join(evs))[:16],
        'status': status,
        'title': title,
        'category': category,
        'evidence_ids': evs,
        'confidence': confidence,
        'reason': reason,
        'limitation': limitation,
        'generated_at': now_iso(),
    }
    if extra: obj.update(extra)
    return obj


def write(findings: list[dict], output: str) -> int:
    report={'schema_version':'info-end-analyzer-output.v1','generated_at':now_iso(),'finding_count':len(findings),'findings':findings}
    text=json.dumps(report, ensure_ascii=False, indent=2)
    if output and output != '-':
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(text, encoding='utf-8')
    else:
        print(text)
    return 0


def by_type(items: list[dict], *keys: str) -> list[dict]:
    return [it for it in items if any(k in str(it.get('discovered_item_type','')) for k in keys)]




def _val(it: dict) -> Any:
    return it.get('discovered_item_value_redacted')

def _extract_route(v: Any) -> str:
    if isinstance(v, dict):
        for k in ['route','resolved_endpoint','endpoint','url','path']:
            if v.get(k): return str(v.get(k))
    if isinstance(v, str): return v
    return ''

def _normalize_path(path: str) -> str:
    path=str(path or '')
    path=re.sub(r'^https?://[^/]+', '', path)
    path=path.split('?')[0]
    path=re.sub(r'\$\{[^}]+\}', ':var', path)
    path=re.sub(r'\{[^}]+\}', ':var', path)
    path=re.sub(r':[A-Za-z_][A-Za-z0-9_]*', ':var', path)
    path=re.sub(r'/+', '/', path)
    return path.rstrip('/') or '/'

def project_fingerprint_analyzer(items: list[dict]) -> list[dict]:
    ev=[it['evidence_id'] for it in items if it.get('linked_report_section') in {'project-fingerprint','technology-stack'}]
    langs=[it for it in items if 'language' in str(it.get('discovered_item_type'))]
    frameworks=[it for it in items if 'framework' in str(it.get('discovered_item_type'))]
    return [finding('candidate','Project fingerprint assembled from local evidence','project_fingerprint',ev[:50],0.74,'Language/framework/project-structure evidence exists in manifest','Static fingerprint can miss generated services or runtime-only modules',{'languages_seen':len(langs),'frameworks_seen':len(frameworks)})] if ev else []


def endpoint_parameter_analyzer(items: list[dict]) -> list[dict]:
    endpoints=by_type(items,'endpoint','route','api_path')
    params=by_type(items,'parameter')
    ev=[it['evidence_id'] for it in endpoints[:50]+params[:50]]
    status='needs_review' if endpoints and params else 'candidate'
    return [finding(status,'Endpoint and parameter surfaces require binding review','endpoint_parameter',ev,0.66,'Endpoint and parameter evidence was collected but exact route-to-handler-to-parameter binding may be incomplete','Analyzer correlates by manifest categories only; framework-specific AST/dataflow may be required',{'endpoint_count':len(endpoints),'parameter_count':len(params)})] if ev else []


def auth_surface_analyzer(items: list[dict]) -> list[dict]:
    auth=[it for it in items if str(it.get('auth_relevance')) not in {'unknown','low',''} or any(w in str(it.get('discovered_item_value_redacted')).lower() for w in ['auth','permission','role','jwt','cookie','session'])]
    ev=[it['evidence_id'] for it in auth[:100]]
    return [finding('needs_review','Authentication and authorization surface signals found','auth_surface',ev,0.62,'Auth-related terms, headers, sessions, permissions or middleware signals appear in evidence','Static signals do not prove bypassability or effective policy',{'signal_count':len(auth)})] if ev else []


def role_tenant_surface_analyzer(items: list[dict]) -> list[dict]:
    rt=[it for it in items if str(it.get('tenant_relevance')) not in {'unknown','low',''} or str(it.get('role_relevance')) not in {'unknown','low',''} or any(w in str(it.get('discovered_item_value_redacted')).lower() for w in ['tenant','orgid','workspace','accountid','projectid','role','admin','permission','policy'])]
    ev=[it['evidence_id'] for it in rt[:120]]
    matrix={}
    boundary_fields=set()
    policy_paths=[]
    for it in rt:
        text=json.dumps(it.get('discovered_item_value_redacted'),ensure_ascii=False,default=str)
        for f in re.findall(r'(?i)\b(tenantId|tenant_id|orgId|organizationId|workspaceId|accountId|projectId|role|roles|permission|permissions|admin|isAdmin)\b', text):
            boundary_fields.add(f)
        route=_normalize_path(_extract_route(it.get('discovered_item_value_redacted')))
        if route and route != '/':
            entry=matrix.setdefault(route, {'roles':set(), 'tenant_fields':set(), 'evidence_ids':[]})
            entry['evidence_ids'].append(it.get('evidence_id'))
            for role in re.findall(r'(?i)\b(admin|owner|member|user|viewer|editor|auditor|superadmin)\b', text): entry['roles'].add(role.lower())
            for fld in boundary_fields: entry['tenant_fields'].add(fld)
            if any(x in text.lower() for x in ['policy','guard','permission','authorize','can?']): policy_paths.append(route)
    serial_matrix={k:{'roles':sorted(v['roles']),'tenant_fields':sorted(v['tenant_fields']),'evidence_ids':v['evidence_ids'][:20]} for k,v in matrix.items()}
    return [finding('needs_review','Role/tenant permission matrix candidate generated','role_tenant_surface',ev,0.68,'Role, permission, tenant and org/workspace/account identifiers were grouped into a candidate permission matrix','Static matrix is not an authorization result; requires multi-role/multi-tenant runtime replay before confirmed access-control conclusions',{'signal_count':len(rt),'boundary_fields':sorted(boundary_fields),'policy_paths':sorted(set(policy_paths)),'permission_matrix_candidate':serial_matrix})] if ev else []

def frontend_backend_correlation_analyzer(items: list[dict]) -> list[dict]:
    frontend=[it for it in items if it.get('linked_report_section')=='frontend-js']
    backend=[it for it in items if it.get('linked_report_section')=='route-api-inventory']
    fe_nodes=[]; be_nodes=[]
    for it in frontend:
        route=_normalize_path(_extract_route(it.get('discovered_item_value_redacted')))
        if route and route != '/': fe_nodes.append({'route':route,'evidence_id':it['evidence_id'],'type':it.get('discovered_item_type'),'value':it.get('discovered_item_value_redacted')})
    for it in backend:
        route=_normalize_path(_extract_route(it.get('discovered_item_value_redacted')))
        if route and route != '/': be_nodes.append({'route':route,'evidence_id':it['evidence_id'],'type':it.get('discovered_item_type'),'value':it.get('discovered_item_value_redacted')})
    matches=[]
    be_by_route={b['route']:b for b in be_nodes}
    for f in fe_nodes:
        candidates=[b for b in be_nodes if f['route']==b['route'] or f['route'].endswith(b['route']) or b['route'].endswith(f['route']) or re.sub(r':var','[^/]+',b['route'])==f['route']]
        if candidates:
            b=candidates[0]
            matches.append({'frontend_route':f['route'],'backend_route':b['route'],'frontend_evidence_id':f['evidence_id'],'backend_evidence_id':b['evidence_id'],'match_kind':'exact_or_template_suffix'})
    denominator=max(1,len(fe_nodes))
    metric={'frontend_api_nodes':len(fe_nodes),'backend_route_nodes':len(be_nodes),'matched_edges':len(matches),'route_to_api_correlation_accuracy':round(len(matches)/denominator,4),'unmatched_frontend_count':max(0,len(fe_nodes)-len(matches))}
    ev=[x['frontend_evidence_id'] for x in matches[:50]]+[x['backend_evidence_id'] for x in matches[:50]]
    if not ev: ev=[it['evidence_id'] for it in (frontend[:30]+backend[:30])]
    return [finding('candidate','Frontend route to backend handler correlation graph generated','frontend_backend_correlation',ev,0.66 if matches else 0.48,'Frontend API callgraph nodes were normalized and matched to backend route evidence; accuracy metric is reported as matched frontend nodes / total frontend API nodes','Static correlation can miss dynamic paths and can match stale/dead code; runtime validation is required for confirmed reachability',{'correlation_graph':{'edges':matches[:200]},'correlation_metrics':metric})] if ev else []

def secret_redaction_analyzer(items: list[dict]) -> list[dict]:
    redacted=[it for it in items if it.get('redaction_status')=='redacted']
    failures=[it for it in items if find_unredacted_secrets(it.get('discovered_item_value_redacted'))]
    ev=[it['evidence_id'] for it in (redacted[:50]+failures[:50])]
    status='needs_review' if failures else 'candidate'
    return [finding(status,'Secret redaction review result','secret_redaction',ev,0.88 if not failures else 0.2,'Evidence redaction status was reviewed for secret-like values','Regex/entropy detectors may miss novel secret formats and may flag placeholders',{'redacted_items':len(redacted),'unredacted_failures':len(failures)})]


def evidence_quality_analyzer(items: list[dict]) -> list[dict]:
    weak=[it for it in items if not it.get('reason') or not it.get('limitation') or str(it.get('source_file','')).lower()=='unknown']
    confirmed=[it for it in items if it.get('finding_status')=='confirmed']
    ev=[it['evidence_id'] for it in (weak[:50]+confirmed[:50])]
    return [finding('needs_review' if weak else 'candidate','Evidence quality analyzer completed','evidence_quality',ev or [items[0]['evidence_id']] if items else [],0.7,'Evidence fields were checked for source/reason/limitation and confirmed claims','Does not replace JSON schema validation or quality gates',{'weak_items':len(weak),'confirmed_items':len(confirmed),'total_items':len(items)})] if items else []

ANALYZERS={
    'project_fingerprint_analyzer': project_fingerprint_analyzer,
    'endpoint_parameter_analyzer': endpoint_parameter_analyzer,
    'auth_surface_analyzer': auth_surface_analyzer,
    'role_tenant_surface_analyzer': role_tenant_surface_analyzer,
    'frontend_backend_correlation_analyzer': frontend_backend_correlation_analyzer,
    'secret_redaction_analyzer': secret_redaction_analyzer,
    'evidence_quality_analyzer': evidence_quality_analyzer,
}


def run_analyzer(name: str) -> int:
    ap=argparse.ArgumentParser(description=f'{name}: analyze Info-End evidence manifest without claiming confirmed vulnerabilities')
    ap.add_argument('--input', required=True, help='Evidence manifest JSON')
    ap.add_argument('--output','-o', default='-')
    a=ap.parse_args()
    data=load_manifest(Path(a.input)); return write(ANALYZERS[name](manifest_items(data)), a.output)
