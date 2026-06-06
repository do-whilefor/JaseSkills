#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, output_report, evidence, dry_run_report, read_text, PATH_RE, URL_RE, line_no
GQL=re.compile(r'\b(query|mutation|subscription)\s+([A-Za-z_][A-Za-z0-9_]*)')
FLAG=re.compile(r'(?i)\b(feature[_-]?flag|experiment|beta|enable[A-Z][A-Za-z0-9_]*|is[A-Z][A-Za-z0-9_]*(Enabled|Active))\b')
def main():
    ap=common_parser('Deep local JS artifact collector: bundles, chunks, sourcemaps, service workers, manifests, hidden APIs, GraphQL operations and feature flags.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope, root); ok,reason=enforce_scope(root, scope)
    if args.dry_run: return dry_run_report(args,'js_deep_info_collector',root,scope)
    if not ok: return output_report(args,'js_deep_info_collector',[evidence('js_deep_info_collector',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    items=[]
    for p in (iter_scoped_files(root, scope, args.max_files, args.timeout, args.scan_profile, args.follow_symlinks) if root.is_dir() else [root]):
        low=p.name.lower(); text=read_text(p)
        if not (low.endswith(('.js','.mjs','.cjs','.jsx','.ts','.tsx','.map','.json')) or 'service-worker' in low or 'manifest' in low): continue
        if low.endswith('.map'):
            items.append(evidence('js_deep_info_collector',p,root,'source_map_artifact',p.name,1,confidence=.95,data_sensitivity='medium',needs_review=True,linked_report_section='frontend-js'))
            try:
                data=json.loads(text)
                for src in data.get('sources',[])[:200]: items.append(evidence('js_deep_info_collector',p,root,'source_map_original_source',src,1,confidence=.9,data_sensitivity='medium',needs_review=True,linked_report_section='frontend-js'))
            except Exception: pass
        if low.endswith(('.js','.mjs','.cjs')) and ('.min.' in low or any(len(x)>500 for x in text.splitlines()[:50])):
            items.append(evidence('js_deep_info_collector',p,root,'minified_js_bundle',p.name,1,confidence=.8,linked_report_section='frontend-js'))
        if 'service-worker' in low or low in {'sw.js','workbox.js'}:
            for m in re.finditer(r'(?i)(precache|addAll|registerRoute|cacheName|url:)\s*[^\n]{0,180}',text): items.append(evidence('js_deep_info_collector',p,root,'service_worker_cache_entry',m.group(0),line_no(text,m.group(0)),confidence=.75,endpoint_relevance='medium',needs_review=True,linked_report_section='frontend-js'))
        if 'manifest' in low:
            for m in PATH_RE.finditer(text): items.append(evidence('js_deep_info_collector',p,root,'manifest_hidden_page_or_asset',m.group(0),line_no(text,m.group(0)),confidence=.65,endpoint_relevance='medium',linked_report_section='frontend-js'))
        for m in PATH_RE.finditer(text): items.append(evidence('js_deep_info_collector',p,root,'frontend_hidden_api_literal',m.group(0),line_no(text,m.group(0)),confidence=.6,endpoint_relevance='medium',needs_review=True,linked_report_section='frontend-js'))
        for m in URL_RE.finditer(text): items.append(evidence('js_deep_info_collector',p,root,'frontend_domain_or_callback',m.group(0),line_no(text,m.group(0)),confidence=.6,endpoint_relevance='medium',needs_review=True,linked_report_section='frontend-js'))
        for m in GQL.finditer(text): items.append(evidence('js_deep_info_collector',p,root,'graphql_operation_in_js',{'type':m.group(1),'name':m.group(2)},line_no(text,m.group(0)),confidence=.75,endpoint_relevance='medium',linked_report_section='frontend-js'))
        for m in FLAG.finditer(text): items.append(evidence('js_deep_info_collector',p,root,'feature_flag_or_test_switch',m.group(0),line_no(text,m.group(0)),confidence=.6,needs_review=True,linked_report_section='frontend-js'))
    return output_report(args,'js_deep_info_collector',items)
if __name__=='__main__': raise SystemExit(main())
