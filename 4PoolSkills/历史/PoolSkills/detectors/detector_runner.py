#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re, sys, datetime
from collections import deque, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import load_scope, iter_scoped_files, read_text_scoped, load_yaml
ROOT=Path(__file__).resolve().parents[1]
def now(): return datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')
def did(*x): return 'finding-'+hashlib.sha256(':'.join(map(str,x)).encode()).hexdigest()[:14]
def line(t,p): return t[:p].count('\n')+1
def _regex_any(patterns, text):
    for pat in patterns or []:
        try: m=re.search(str(pat), text or '', re.I)
        except re.error: m=re.search(re.escape(str(pat)), text or '', re.I)
        if m: return m
    return None

def _graph_index(graph):
    nodes={n['id']:n for n in graph.get('nodes',[])}
    adj=defaultdict(list)
    for e in graph.get('edges',[]): adj[e.get('from')].append(e)
    return nodes, adj

def _is_source_node(n):
    return n.get('type') in {'route','source','parameter','handler'}

def _path_to_sink(nodes, adj, sink_id, max_depth=10):
    starts=[nid for nid,n in nodes.items() if _is_source_node(n)]
    q=deque((s,[s]) for s in starts)
    seen={(s,0) for s in starts}
    while q:
        cur,path=q.popleft()
        if cur==sink_id and len(path)>1:
            return path
        if len(path)>max_depth: continue
        for e in adj.get(cur,[]):
            nxt=e.get('to')
            key=(nxt,len(path))
            if nxt in nodes and key not in seen:
                seen.add(key); q.append((nxt,path+[nxt]))
    return None

def _path_summary(nodes, ids):
    out=[]
    for nid in ids or []:
        n=nodes.get(nid,{})
        data=n.get('data') or {}
        out.append({'node_id':nid,'kind':n.get('type'),'label':n.get('label'),'file':data.get('file') or data.get('path'),'line':data.get('line')})
    return out

def _route_context(nodes, ids):
    routes=[]; roles=[]; tenants=[]
    for nid in ids or []:
        n=nodes.get(nid,{})
        if n.get('type')=='route': routes.append(n.get('data',{}))
        label=(n.get('label') or '') + ' ' + json.dumps(n.get('data',{}),ensure_ascii=False)
        if re.search(r'admin|manager|user|anonymous|role|permission', label, re.I): roles.append(label[:120])
        if re.search(r'tenant|org|workspace|x-tenant', label, re.I): tenants.append(label[:120])
    return routes, roles, tenants

def detect(root, graph_file=None, rules_file=None, scope_file=None):
    root=Path(root).resolve(); scope=load_scope(root,scope_file); rules=load_yaml(rules_file or ROOT/'detectors/detector_rules.yaml')['rules']
    graph=json.loads(Path(graph_file).read_text(encoding='utf-8')) if graph_file else {'nodes':[],'edges':[]}
    nodes,adj=_graph_index(graph)
    sink_nodes=[n for n in graph.get('nodes',[]) if n.get('type')=='sink']
    findings=[]

    # Cross-file/source-to-sink graph pass.
    for rule in rules:
        for sn in sink_nodes:
            label=sn.get('label','')
            sink_match = bool(rule.get('sink_patterns') and _regex_any(rule.get('sink_patterns'), label))
            file_match = False
            data=sn.get('data',{})
            rel=data.get('file')
            if rel and rule.get('file_patterns'):
                try:
                    text,_=read_text_scoped(root/rel,root,scope,limit=200_000)
                    file_match=bool(_regex_any(rule.get('file_patterns'), text))
                except Exception:
                    file_match=False
            if not (sink_match or file_match):
                continue
            ids=_path_to_sink(nodes,adj,sn['id'])
            if not ids:
                continue
            routes,roles,tenants=_route_context(nodes,ids)
            fid=did(rule['id'],rel,data.get('line'),label,'graphpath')
            findings.append(make_finding(rule,fid,root,rel,data.get('line'),source='cross_file_dataflow',sink=label,evidence_summary=f"source-to-sink graph path to {label}",dataflow=_path_summary(nodes,ids),routes=routes,roles=roles,tenants=tenants))

    # Static scoped file signal pass for detectors that have no sink node.
    for rule in rules:
        for p in iter_scoped_files(root,scope):
            if p.suffix.lower() not in {'.py','.js','.jsx','.ts','.tsx','.java','.php','.rb','.go','.rs','.yml','.yaml','.json','.tf','.sh','.env','.properties'}: continue
            text,_=read_text_scoped(p,root,scope,limit=1_000_000); rel=str(p.relative_to(root))
            m=_regex_any(rule.get('file_patterns'), text)
            if m:
                fid=did(rule['id'],rel,line(text,m.start()),m.group(0),'filesignal')
                findings.append(make_finding(rule,fid,root,rel,line(text,m.start()),source='source_scan',sink=rule.get('sink_patterns',[None])[0],evidence_summary=m.group(0)[:120],dataflow=[{'kind':'file','path':rel,'line':line(text,m.start())},{'kind':'signal','name':rule['id']}]))

    # de-duplicate while preserving stronger cross_file_dataflow result.
    best={}
    for f in findings:
        key=(f['detector_id'],tuple((x.get('path'),x.get('line')) for x in f['affected_files']))
        old=best.get(key)
        if not old or (old['source']!='cross_file_dataflow' and f['source']=='cross_file_dataflow'):
            best[key]=f
    out=list(best.values())
    return {'schema_version':'finding-candidates-v1','generated_at':now(),'scope':{'root':str(root),'mode':'local_authorized_static'},'findings':out,'summary':{'findings':len(out),'confirmed':0,'policy':'detectors emit candidates only; confirmation requires dynamic quality gate','cross_file_dataflow':sum(1 for f in out if f['source']=='cross_file_dataflow')}}

def make_finding(rule,fid,root,file,line_no,source,sink,evidence_summary,dataflow=None,routes=None,roles=None,tenants=None):
    ev_id='ev-'+hashlib.sha256(f'{fid}:{file}:{line_no}'.encode()).hexdigest()[:14]
    auth_context={'required':'unknown'}
    tenant_context={'required':'unknown'}
    if roles: auth_context={'role':'matrix_required','observed_signals':roles[:3]}
    if tenants: tenant_context={'tenant':'matrix_required','observed_signals':tenants[:3]}
    affected_routes=[]
    for r in routes or []:
        affected_routes.append({'route_id':r.get('route_id'),'method':r.get('method'),'path':r.get('path'),'file':r.get('file')})
    blockers=['dynamic_request_missing','dynamic_response_missing','screenshot_or_dom_missing','negative_test_missing','quality_gate_not_passed']
    if rule.get('requires_role_tenant'): blockers.append('role_tenant_matrix_missing')
    return {'finding_id':fid,'detector_id':rule['id'],'title':rule['title'],'severity_candidate':rule.get('severity_candidate','medium'),'confidence':'medium' if source!='cross_file_dataflow' else 'high','affected_files':[{'path':file,'line':line_no}],'affected_routes':affected_routes,'source':source,'sink':sink or 'unknown','dataflow_path':dataflow or [{'kind':'file','path':file,'line':line_no},{'kind':'sink','name':sink or rule['id']}],'auth_context':auth_context,'tenant_context':tenant_context,'required_role':'matrix_required' if rule.get('requires_role_tenant') else 'unknown','evidence_refs':[ev_id],'replay_plan_id':'rp-'+fid,'negative_test_id':'neg-'+fid,'blocked_test_id':'blk-'+fid,'review_status':'candidate','confirmed_blockers':blockers,'false_positive_checks':['verify cross-file source-to-sink reachability','verify input is user-controlled','verify non-destructive dynamic replay','verify authorization and tenant context','verify sanitized evidence refs exist'],'non_destructive':True,'evidence_inline':[{'evidence_id':ev_id,'type':'source_line','source_file':file,'line':line_no,'summary':evidence_summary}]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('root'); ap.add_argument('--graph'); ap.add_argument('--rules'); ap.add_argument('--scope-file'); ap.add_argument('--out',required=True)
    ns=ap.parse_args(); data=detect(ns.root,ns.graph,ns.rules,ns.scope_file)
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(data['summary'],ensure_ascii=False))
if __name__=='__main__': main()
