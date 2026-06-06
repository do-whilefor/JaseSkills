#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, dry_run_report, output_report, evidence, read_text, line_no, stable_hash
AUTH_RE=re.compile(r'(?i)(requireAuth|authenticate|authorize|isAuthenticated|isAdmin|hasRole|permission|policy|guard|middleware|before_action|Depends\s*\(.*auth|Security\s*\()')
ROLE_RE=re.compile(r'(?i)\b(admin|owner|member|viewer|editor|superuser|staff|role|permission|scope|policy)\b')
TENANT_RE=re.compile(r'(?i)\b(tenant_id|tenant|org_id|organization_id|workspace_id|account_id|company_id|owner_id|created_by|user_id)\b')
HANDLER_RE=re.compile(r'(?m)^\s*(?:async\s+)?(?:def|function)\s+([A-Za-z_][A-Za-z0-9_]*)|(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\(')

def node(nodes, typ, label, meta=None):
    nid=f'{typ}:{stable_hash(label)[:12]}'
    nodes.setdefault(nid, {'id':nid,'type':typ,'label':label,'meta':meta or {}})
    return nid

def main():
    ap=common_parser('Build candidate auth graph from middleware, decorators, policies, roles, tenants and owner fields.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope,root); ok,reason=enforce_scope(root,scope)
    if args.dry_run: return dry_run_report(args,'auth_graph_builder',root,scope)
    if not ok: return output_report(args,'auth_graph_builder',[evidence('auth_graph_builder',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    nodes={}; edges=[]; items=[]
    for p in (iter_scoped_files(root,scope,args.max_files,args.timeout,args.scan_profile,args.follow_symlinks) if root.is_dir() else [root]):
        text=read_text(p)
        file_node=node(nodes,'SourceFile',str(p.relative_to(root)) if root.is_dir() else p.name)
        for m in HANDLER_RE.finditer(text):
            h=m.group(1) or m.group(2); hnode=node(nodes,'Handler',h,{'source_file':str(p)}); edges.append({'from':file_node,'to':hnode,'relation':'defines_handler'})
        for regex,typ,rel in [(AUTH_RE,'AuthPolicy','mentions_auth'),(ROLE_RE,'RoleOrPermission','mentions_role'),(TENANT_RE,'TenantOrOwnerField','mentions_tenant')]:
            for m in regex.finditer(text):
                label=m.group(0); n=node(nodes,typ,label,{'source_file':str(p),'line':line_no(text,label)}); edges.append({'from':file_node,'to':n,'relation':rel})
                items.append(evidence('auth_graph_builder',p,root,'auth_graph_edge',{'node_type':typ,'label':label,'relation':rel},line_no(text,label),confidence=.58,auth_relevance='high' if typ=='AuthPolicy' else 'medium',tenant_relevance='high' if typ=='TenantOrOwnerField' else 'medium',role_relevance='high' if typ=='RoleOrPermission' else 'medium',scope_id=scope['scope_id'],needs_review=True,linked_report_section='auth-role-tenant'))
    graph={'schema_version':'auth-graph.v1','nodes':list(nodes.values()),'edges':edges,'quality_note':'Candidate static graph; runtime role/tenant replay is still required before confirming authorization impact.'}
    return output_report(args,'auth_graph_builder',items,{'graph':graph})
if __name__=='__main__': raise SystemExit(main())
