#!/usr/bin/env python3
import argparse, csv, json, re, sys
from pathlib import Path
from urllib.parse import urlparse
ROUTE_RE=re.compile("(?ix)(?:https?://[^\\s\'\"`<>]+)|(?:[A-Z]{3,7}\\s+/[A-Za-z0-9_./{}:$?&=%\\-]+)|(?:/[A-Za-z0-9_./{}:$?&=%\\-]{1,})")
METHOD_RE=re.compile(r'\b(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\b',re.I)
def norm_path(s):
    s=str(s).strip().strip('`"\'')
    if not s:return None
    parts=s.split(); method=None
    if parts and METHOD_RE.fullmatch(parts[0]): method=parts[0].upper(); s=parts[1] if len(parts)>1 else ''
    if s.startswith(('http://','https://')): u=urlparse(s); s=u.path or '/'
    if not s.startswith('/'): return None
    s=re.sub(r'\?.*$','',s); s=re.sub(r'/+','/',s); s=s.rstrip('/') if len(s)>1 else s
    return (method or '*',s)
def load_file(path):
    if not path: return set()
    p=Path(path)
    if not p.exists(): print(f'[WARN] missing input: {path}',file=sys.stderr); return set()
    text=p.read_text(errors='ignore'); items=set()
    if p.suffix.lower() in ('.jsonl','.ndjson'):
        for line in text.splitlines():
            try: obj=json.loads(line)
            except Exception: continue
            for key in ('url','path','route','endpoint'):
                if key in obj:
                    np=norm_path(str(obj.get('method','*'))+' '+str(obj[key]));
                    if np: items.add(np)
    elif p.suffix.lower()=='.json':
        try:
            data=json.loads(text); stack=data if isinstance(data,list) else [data]
            while stack:
                obj=stack.pop()
                if isinstance(obj,dict):
                    val=next((obj.get(k) for k in ('url','path','route','endpoint') if k in obj),None)
                    if val:
                        np=norm_path(str(obj.get('method','*'))+' '+str(val));
                        if np: items.add(np)
                    stack.extend(obj.values())
                elif isinstance(obj,list): stack.extend(obj)
                elif isinstance(obj,str):
                    np=norm_path(obj);
                    if np: items.add(np)
        except Exception: pass
    elif p.suffix.lower()=='.csv':
        for row in csv.DictReader(text.splitlines()):
            val=next((row.get(k) for k in ('url','path','route','endpoint') if row.get(k)),None)
            if val:
                np=norm_path(str(row.get('method','*'))+' '+val)
                if np: items.add(np)
    for m in ROUTE_RE.finditer(text):
        np=norm_path(m.group(0))
        if np: items.add(np)
    return items
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--source'); ap.add_argument('--frontend'); ap.add_argument('--runtime'); ap.add_argument('--docs'); ap.add_argument('--out',default='shadow-ledger-diff.md'); args=ap.parse_args()
    ledgers={k:load_file(getattr(args,k)) for k in ('source','frontend','runtime','docs')}; all_items=set().union(*ledgers.values()) if ledgers else set(); rows=[]
    for item in sorted(all_items,key=lambda t:(t[1],t[0])): rows.append((item,{k:item in v for k,v in ledgers.items()}))
    def only(name): return [i for i,p in rows if p[name] and sum(p.values())==1]
    def missing_runtime(): return [i for i,p in rows if (p['source'] or p['frontend'] or p['docs']) and not p['runtime']]
    def runtime_only(): return [i for i,p in rows if p['runtime'] and not (p['source'] or p['frontend'] or p['docs'])]
    out=['# 资产影子账本 Diff\n','## 输入规模\n']
    for k,v in ledgers.items(): out.append(f'- {k}: {len(v)}')
    out+=['\n## 四表总览\n','| Method | Path | Source | Frontend | Runtime | Docs | 状态提示 |','|---|---|---|---|---|---|---|']
    for (method,path),p in rows:
        hint=[]
        if (p['source'] or p['frontend'] or p['docs']) and not p['runtime']: hint.append('静态/文档有线索，待动态验证')
        if p['runtime'] and not (p['source'] or p['frontend'] or p['docs']): hint.append('运行态孤岛，需找代码/配置来源')
        if p['frontend'] and not p['source']: hint.append('前端引用但后端来源未定位')
        out.append(f'| {method} | `{path}` | {"Y" if p["source"] else ""} | {"Y" if p["frontend"] else ""} | {"Y" if p["runtime"] else ""} | {"Y" if p["docs"] else ""} | {"; ".join(hint)} |')
    out.append('\n## 差集清单\n')
    for title,items in [('仅源码出现',only('source')),('仅前端出现',only('frontend')),('仅运行态出现',only('runtime')),('仅文档出现',only('docs')),('缺运行态验证',missing_runtime()),('运行态孤岛',runtime_only())]:
        out.append(f'### {title}\n'); out.extend([f'- {m} `{p}`' for m,p in items[:300]] or ['- 无']); out.append('')
    out+=['## 使用提示\n','- 差集不是漏洞，只是下一轮最小动态验证清单。','- “缺运行态验证”应回流 04；“运行态孤岛”应回流 03 寻找代码/配置来源；角色差异应回流 05。']
    Path(args.out).write_text('\n'.join(out),encoding='utf-8'); print(f'Wrote {args.out}')
if __name__=='__main__': main()
