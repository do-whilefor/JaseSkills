#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, dry_run_report, output_report, evidence, read_text, line_no, URL_RE, PATH_RE, stable_hash
GQL=re.compile(r'\b(query|mutation|subscription)\s+([A-Za-z_][A-Za-z0-9_]*)')
BASE=re.compile(r"""(?i)(baseURL|apiBase|endpoint|graphqlUrl|socketUrl)\s*[:=]\s*[`"']([^`"']+)""")
CACHE=re.compile(r"""caches\.(?:open|match|addAll)\s*\(|self\.addEventListener\s*\(\s*[`"'](install|fetch|activate)""")

def n(nodes, typ, label, meta=None):
    nid=f'{typ}:{stable_hash(label)[:12]}'
    nodes.setdefault(nid,{'id':nid,'type':typ,'label':label,'meta':meta or {}})
    return nid

def main():
    ap=common_parser('Build frontend artifact graph for chunks, source maps, service workers, manifests, base URLs and GraphQL operations.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope,root); ok,reason=enforce_scope(root,scope)
    if args.dry_run: return dry_run_report(args,'frontend_artifact_graph',root,scope)
    if not ok: return output_report(args,'frontend_artifact_graph',[evidence('frontend_artifact_graph',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    items=[]; nodes={}; edges=[]
    for p in (iter_scoped_files(root,scope,args.max_files,args.timeout,'frontend-artifacts',args.follow_symlinks) if root.is_dir() else [root]):
        text=read_text(p); rel=str(p.relative_to(root)) if root.is_dir() else p.name; file_node=n(nodes,'FrontendArtifact',rel,{'suffix':p.suffix})
        if p.suffix=='.map':
            try:
                data=json.loads(text); sources=data.get('sources') or []
                items.append(evidence('frontend_artifact_graph',p,root,'source_map_artifact',{'sources':sources[:50],'has_sources_content':bool(data.get('sourcesContent'))},1,confidence=.9,endpoint_relevance='medium',scope_id=scope['scope_id'],needs_review=True,linked_report_section='frontend-js'))
                for src in sources[:200]: edges.append({'from':file_node,'to':n(nodes,'OriginalSource',src),'relation':'maps_to_source'})
                for content in data.get('sourcesContent') or []:
                    for m in PATH_RE.finditer(str(content)):
                        ep=n(nodes,'Endpoint',m.group(0)); edges.append({'from':file_node,'to':ep,'relation':'sourcesContent_mentions_endpoint'})
            except Exception: pass
        if 'service-worker' in p.name.lower() or 'sw.' in p.name.lower():
            if CACHE.search(text): items.append(evidence('frontend_artifact_graph',p,root,'service_worker_cache_logic','service worker cache/fetch event',1,confidence=.8,endpoint_relevance='medium',scope_id=scope['scope_id'],needs_review=True,linked_report_section='frontend-js'))
        if p.name.lower() in {'manifest.json','asset-manifest.json'}:
            items.append(evidence('frontend_artifact_graph',p,root,'frontend_manifest_artifact',rel,1,confidence=.85,scope_id=scope['scope_id'],linked_report_section='frontend-js'))
        for regex,typ in [(PATH_RE,'frontend_artifact_endpoint'),(URL_RE,'frontend_artifact_url')]:
            for m in regex.finditer(text):
                items.append(evidence('frontend_artifact_graph',p,root,typ,m.group(0),line_no(text,m.group(0)),confidence=.6,endpoint_relevance='medium',scope_id=scope['scope_id'],needs_review=True,linked_report_section='frontend-js'))
                edges.append({'from':file_node,'to':n(nodes,'EndpointOrURL',m.group(0)),'relation':'mentions'})
        for m in GQL.finditer(text):
            items.append(evidence('frontend_artifact_graph',p,root,'graphql_operation',{'operation_type':m.group(1),'name':m.group(2)},line_no(text,m.group(0)),confidence=.72,endpoint_relevance='medium',scope_id=scope['scope_id'],linked_report_section='frontend-js'))
        for m in BASE.finditer(text):
            items.append(evidence('frontend_artifact_graph',p,root,'frontend_base_url_or_endpoint_setting',{m.group(1):m.group(2)},line_no(text,m.group(0)),confidence=.7,endpoint_relevance='medium',scope_id=scope['scope_id'],needs_review=True,linked_report_section='frontend-js'))
    return output_report(args,'frontend_artifact_graph',items,{'graph':{'schema_version':'frontend-artifact-graph.v1','nodes':list(nodes.values()),'edges':edges}})
if __name__=='__main__': raise SystemExit(main())
