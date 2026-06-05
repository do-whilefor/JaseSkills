#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess, sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

SOURCES = [
    ('location_hash', re.compile(r'\b(location\.(?:href|hash|search)|document\.URL|document\.referrer)\b')),
    ('postmessage_data', re.compile(r'\bmessage\s*\.\s*data\b|addEventListener\s*\(\s*["\']message')),
    ('storage_value', re.compile(r'\b(?:localStorage|sessionStorage)\.(?:getItem|\w+)\b|indexedDB')),
    ('cookie_value', re.compile(r'\bdocument\.cookie\b')),
    ('graphql_variables', re.compile(r'\bvariables\s*[:=]')),
    ('websocket_message', re.compile(r'\bWebSocket\b|\.onmessage\b')),
]
SINKS = [
    ('dom_xss_html', re.compile(r'\b(innerHTML|outerHTML|insertAdjacentHTML|dangerouslySetInnerHTML|srcdoc)\b')),
    ('code_execution', re.compile(r'\b(eval|Function|setTimeout|setInterval)\s*\(')),
    ('script_injection', re.compile(r'createElement\s*\(\s*["\']script|\.src\s*=')),
    ('open_redirect', re.compile(r'\b(location\.(?:href|assign|replace)|window\.open)\b')),
    ('postmessage_sink', re.compile(r'\.postMessage\s*\(')),
    ('prototype_pollution', re.compile(r'(__proto__|constructor\s*\]|prototype\s*\]|merge\s*\(|assign\s*\()')),
    ('network_sink', re.compile(r'\b(fetch|axios\.|XMLHttpRequest|WebSocket|EventSource)\b')),
    ('graphql_mutation', re.compile(r'\bmutation\s+[A-Za-z0-9_]*|gql\s*`[^`]*mutation', re.S)),
]
AUTH_PATTERNS = [
    ('authorization_header', re.compile(r'Authorization|Bearer|X-CSRF|X-XSRF|csrf', re.I)),
    ('tenant_header_or_id', re.compile(r'X-Tenant|tenantId|orgId|workspaceId|companyId', re.I)),
    ('role_guard', re.compile(r'role|permission|isAdmin|can\(|hasPermission|featureFlag', re.I)),
    ('jwt_logic', re.compile(r'jwt|refreshToken|accessToken|idToken|kid|alg', re.I)),
    ('oauth_logic', re.compile(r'redirect_uri|state|nonce|PKCE|code_verifier|code_challenge', re.I)),
]
SEVERE_RULES = [
    ('JS-HIGH-001','Source Map / sourcesContent leak','source_map_reference|secret_candidate|hidden_route'),
    ('JS-HIGH-002','Hidden admin/internal endpoint','hidden_route_candidate|endpoint_candidate'),
    ('JS-HIGH-003','Client-side role/tenant guard clue','role_guard|tenant_header_or_id'),
    ('JS-HIGH-004','GraphQL hidden mutation/query clue','graphql_operation_candidate|graphql_mutation'),
    ('JS-HIGH-005','WebSocket authz/tenant replay required','websocket_candidate|websocket_message'),
    ('JS-HIGH-006','postMessage token/account takeover clue','postmessage_candidate|postmessage_data|postmessage_sink'),
    ('JS-HIGH-007','OAuth/JWT flow weakness clue','oauth_logic|jwt_logic'),
    ('JS-HIGH-008','DOM XSS source/sink proximity candidate','dom_xss_html|location_hash|storage_value'),
    ('JS-HIGH-009','Prototype pollution gadget clue','prototype_pollution'),
    ('JS-HIGH-010','Service Worker / stale cache poisoning clue','service_worker'),
    ('JS-HIGH-011','Electron/Extension/WebView bridge clue','ipcRenderer|contextBridge|externally_connectable|addJavascriptInterface'),
    ('JS-HIGH-012','Dependency/supply-chain risk clue','postinstall|prepare|private registry|@company'),
]

@dataclass
class BackendStatus:
    name: str
    status: str
    command: str | None
    evidence: str
    reason: str

@dataclass
class Finding:
    finding_id: str
    rule_id: str
    title: str
    status: str
    asset_path: str
    evidence_path: str
    line: int | None
    backend: str
    source: str | None
    sink: str | None
    dynamic_validation: str
    role_tenant_replay: str
    report_section: str
    reason: str


def read_json(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))

def read_text(p: Path):
    for enc in ('utf-8','utf-8-sig','latin-1'):
        try: return p.read_text(encoding=enc, errors='replace')
        except Exception: pass
    return p.read_text(errors='replace')

def line_no(text: str, idx:int)->int:
    return text.count('\n',0,idx)+1

def check_node_module(module: str) -> bool:
    node=shutil.which('node')
    if not node: return False
    code=f"try{{require.resolve('{module}'); process.exit(0)}}catch(e){{process.exit(1)}}"
    return subprocess.run([node,'-e',code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

def backend_status(root: Path) -> list[BackendStatus]:
    node=shutil.which('node')
    statuses=[]
    statuses.append(BackendStatus('node', 'ready' if node else 'missing', node, 'which node' if node else '', 'Node.js is required for JS parser backends'))
    for name, mod in [('babel_parser','@babel/parser'),('babel_traverse','@babel/traverse'),('typescript_compiler_api','typescript')]:
        ok=check_node_module(mod)
        statuses.append(BackendStatus(name, 'ready' if ok else 'missing', f'node require.resolve({mod})', f'require.resolve({mod})' if ok else '', 'Required for semantic AST extraction; missing means candidate-only fallback'))
    # tree-sitter python/node may vary; do not fake ready.
    ts_ok=False
    try:
        import tree_sitter # type: ignore
        ts_ok=True
    except Exception:
        ts_ok=False
    statuses.append(BackendStatus('tree_sitter_javascript','ready' if ts_ok else 'missing','python import tree_sitter','python import tree_sitter' if ts_ok else '', 'Required for alternate parser backend; not used unless grammar is configured'))
    return statuses

def run_node_backend(js_path: Path, backend_script: Path, required_module: str) -> dict[str,Any] | None:
    node=shutil.which('node')
    if not node or not backend_script.exists() or not check_node_module(required_module):
        return None
    proc=subprocess.run([node, str(backend_script), str(js_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if proc.returncode != 0:
        return {'backend': backend_script.name, 'error':proc.stderr[:4000], 'file':str(js_path)}
    try:
        data=json.loads(proc.stdout); data['backend']=backend_script.name; return data
    except Exception as e: return {'backend': backend_script.name, 'error':f'bad backend json: {e}', 'raw':proc.stdout[:1000]}

def candidate_scan(asset: dict[str,Any], root: Path) -> tuple[list[Finding], dict[str,Any]]:
    p=root/asset['path']
    findings=[]; summary={'sources':[], 'sinks':[], 'auth':[], 'has_source_sink_proximity':False}
    if not p.exists() or p.suffix.lower() not in {'.js','.mjs','.cjs','.jsx','.ts','.tsx'}:
        return findings, summary
    text=read_text(p)
    src_hits=[]; sink_hits=[]; auth_hits=[]
    for name, rgx in SOURCES:
        for m in rgx.finditer(text): src_hits.append((name,line_no(text,m.start()),m.group(0)[:160]))
    for name, rgx in SINKS:
        for m in rgx.finditer(text): sink_hits.append((name,line_no(text,m.start()),m.group(0)[:160]))
    for name, rgx in AUTH_PATTERNS:
        for m in rgx.finditer(text): auth_hits.append((name,line_no(text,m.start()),m.group(0)[:160]))
    summary={'sources':src_hits[:100], 'sinks':sink_hits[:100], 'auth':auth_hits[:100], 'has_source_sink_proximity':False}
    # proximity heuristic; candidate-only, not dataflow
    for sn,sl,sv in src_hits:
        for tn,tl,tv in sink_hits:
            if abs(sl-tl) <= 30:
                summary['has_source_sink_proximity']=True
                findings.append(Finding(f'CAND-{len(findings)+1:04d}','JS-CAND-SOURCE-SINK','Candidate source/sink proximity, not proven dataflow','candidate-only',asset['path'],asset['path'],tl,'regex-candidate',sn,tn,'未动态验证','缺少 role/tenant replay','js-analysis-candidates','Regex proximity only; requires AST CFG/DFG and dynamic replay'))
    for an,al,av in auth_hits:
        findings.append(Finding(f'CAND-{len(findings)+1:04d}','JS-CAND-AUTH-TENANT','Auth/tenant/role logic clue','candidate-only',asset['path'],asset['path'],al,'regex-candidate',an,None,'未动态验证','缺少 role/tenant replay','auth-tenant-candidates','Auth keyword clue; requires resolver and role/tenant diff'))
    return findings, summary

def build_findings(ledger: dict[str,Any], root: Path, out: Path, backends: list[BackendStatus]) -> dict[str,Any]:
    findings=[]; ast_results=[]; summaries=[]
    backend_dir=Path(__file__).resolve().parent/'backends/js'
    babel_script=backend_dir/'babel_extract.mjs'
    ts_script=backend_dir/'typescript_extract.mjs'
    ast_ready=any(b.name=='babel_parser' and b.status=='ready' for b in backends) or any(b.name=='typescript_compiler_api' and b.status=='ready' for b in backends)
    for asset in ledger.get('assets',[]):
        if asset.get('kind') in {'javascript','service_worker'}:
            cand, summary=candidate_scan(asset, root)
            summaries.append({'asset':asset['path'], **summary})
            findings.extend(cand)
            if ast_ready:
                res=run_node_backend(root/asset['path'], babel_script, '@babel/parser')
                if not res:
                    res=run_node_backend(root/asset['path'], ts_script, 'typescript')
                if res: ast_results.append(res)
        if asset.get('kind') == 'sourcemap':
            related=asset.get('related',{})
            if related.get('has_sourcesContent'):
                findings.append(Finding(f'CAND-{len(findings)+1:04d}','JS-HIGH-001','Source map sourcesContent leak candidate','candidate-only',asset['path'],asset['path'],None,'sourcemap-parser',None,None,'未动态验证','缺少 role/tenant replay','source-map-leaks','sourcesContent exists; review leaked routes/secrets and map to backend validation'))
        if asset.get('kind') == 'service_worker':
            findings.append(Finding(f'CAND-{len(findings)+1:04d}','JS-HIGH-010','Service Worker cache poisoning/stale asset review required','candidate-only',asset['path'],asset['path'],None,'collector',None,None,'未动态验证','缺少 role/tenant replay','service-worker','Requires cache replay and stale build comparison'))
    # Evidence entries from collector also become severe candidates when matching known risk kinds.
    for ev in ledger.get('evidence',[]):
        kind=ev.get('kind','')
        title_map={
            'secret_candidate':'Secret/config exposure candidate',
            'hidden_route_candidate':'Hidden admin/internal/API route candidate',
            'graphql_operation_candidate':'GraphQL operation candidate',
            'websocket_candidate':'WebSocket schema/authz replay required',
            'postmessage_candidate':'postMessage origin/data validation candidate',
            'public_env_key':'Public build env exposure candidate',
        }
        if kind in title_map:
            findings.append(Finding(f'CAND-{len(findings)+1:04d}', 'JS-COLLECT-'+kind.upper(), title_map[kind], 'candidate-only', ev.get('file',''), ev.get('file',''), ev.get('line'), 'collector-regex', None, None, '未动态验证', '缺少 role/tenant replay', 'collection-risk-candidates', 'Collection evidence is not vulnerability proof; needs resolver and non-destructive validation'))
    analysis={
        'schema_version':'js-top-tier-analysis/v1',
        'backend_status':[asdict(b) for b in backends],
        'semantic_status':'ready' if ast_ready and ast_results else 'candidate-only',
        'semantic_warning': '' if ast_ready and ast_results else 'No confirmed AST backend result; regex findings remain candidate-only and cannot be called semantic audit.',
        'asset_summaries':summaries,
        'ast_results':ast_results,
        'findings':[asdict(f) for f in findings],
        'dynamic_validation':'未动态验证',
        'role_tenant_replay':'缺少 role/tenant replay',
    }
    out.mkdir(parents=True, exist_ok=True)
    (out/'js_analysis.json').write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding='utf-8')
    (out/'js_findings.json').write_text(json.dumps({'schema_version':'js-top-tier-findings/v1','findings':[asdict(f) for f in findings]}, ensure_ascii=False, indent=2), encoding='utf-8')
    return analysis

def main():
    ap=argparse.ArgumentParser(description='Top-tier JS analysis/audit orchestrator with strict candidate-only downgrade')
    ap.add_argument('--ledger', required=True)
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args()
    ledger_path=Path(args.ledger).resolve(); out=Path(args.out).resolve()
    ledger=read_json(ledger_path)
    root=Path(ledger.get('root') or ledger_path.parent).resolve()
    bs=backend_status(root)
    analysis=build_findings(ledger,root,out,bs)
    print(json.dumps({'ok':True,'out':str(out/'js_analysis.json'),'semantic_status':analysis['semantic_status'],'findings':len(analysis['findings']),'backends':analysis['backend_status']}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()
