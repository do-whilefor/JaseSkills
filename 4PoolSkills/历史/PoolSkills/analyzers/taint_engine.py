#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict, deque
from pathlib import Path

def _idx(graph: dict):
    nodes={n['id']:n for n in graph.get('nodes',[])}
    adj=defaultdict(list); rev=defaultdict(list)
    for e in graph.get('edges',[]):
        adj[e.get('from')].append(e); rev[e.get('to')].append(e)
    return nodes, adj, rev

def _is_source(n): return n.get('type') in {'route','source','parameter','handler'}
def _is_sink(n): return n.get('type') == 'sink'
def _is_sanitizer(n):
    label=(n.get('label') or '').lower()
    return any(x in label for x in ['sanitize','escape','validate','parameterized','preparedstatement','safe_join'])

def _type_context(n):
    d=n.get('data') or {}; label=(n.get('label') or '') + ' ' + json.dumps(d,ensure_ascii=False)
    ctx=[]
    for token in ['tenant','org','workspace','role','permission','admin','user','jwt','oauth','graphql','websocket']:
        if token in label.lower(): ctx.append(token)
    return sorted(set(ctx))

def find_taint_paths(graph: dict, max_depth: int = 14) -> dict:
    nodes, adj, rev = _idx(graph)
    paths=[]
    for sid, sn in nodes.items():
        if not _is_source(sn): continue
        q=deque([(sid,[sid],False)])
        seen={(sid,False)}
        while q:
            cur,path,sanitized=q.popleft()
            if len(path) > max_depth: continue
            cn=nodes.get(cur,{})
            sanitized = sanitized or _is_sanitizer(cn)
            if _is_sink(cn) and len(path) > 1:
                paths.append({'source_id':sid,'sink_id':cur,'sanitized':sanitized,'node_ids':path,'nodes':[{'id':x,'type':nodes[x].get('type'),'label':nodes[x].get('label'),'file':(nodes[x].get('data') or {}).get('file'),'line':(nodes[x].get('data') or {}).get('line')} for x in path], 'context':sorted(set(sum((_type_context(nodes[x]) for x in path), [])))})
                continue
            for e in adj.get(cur,[]):
                nxt=e.get('to')
                key=(nxt,sanitized)
                if nxt in nodes and key not in seen:
                    seen.add(key); q.append((nxt,path+[nxt],sanitized))
    return {'schema_version':'taint-analysis-v1','paths':paths,'summary':{'paths':len(paths),'unsanitized_paths':sum(1 for p in paths if not p['sanitized'])},'policy':'Name-based call graph plus AST nodes; confirmed still requires replay and manifest-backed dynamic evidence.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--graph',required=True); ap.add_argument('--out',required=True); ns=ap.parse_args()
    data=find_taint_paths(json.loads(Path(ns.graph).read_text(encoding='utf-8')))
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(data['summary'],ensure_ascii=False))
if __name__=='__main__': main()
