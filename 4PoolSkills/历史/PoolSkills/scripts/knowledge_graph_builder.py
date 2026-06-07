#!/usr/bin/env python3
import argparse,json,re
from pathlib import Path
S={'file_read':['readFile','fs.read','open('],'file_write':['writeFile','createWriteStream'],'command':['exec(','spawn(','subprocess','Runtime.exec','system('],'network':['fetch(','axios','requests.'],'raw_query':['raw(','query(','DB::raw']}
def load(p):
 p=Path(p); return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--routes',default='outputs/attack_surface.json'); ap.add_argument('--js',default='outputs/js_assets.json'); ap.add_argument('--out',default='outputs/code_graph.json'); a=ap.parse_args(); r=Path(a.project); routes=load(a.routes).get('routes',[]); js=load(a.js); sinks=[]
 for p in r.rglob('*'):
  if any(x in p.parts for x in ['.git','node_modules','vendor','target','dist']): continue
  if not p.is_file() or p.suffix.lower() not in ['.js','.ts','.py','.java','.php','.rb','.go','.rs']: continue
  txt=p.read_text(encoding='utf-8',errors='ignore'); rel=str(p.relative_to(r))
  for typ,pats in S.items():
   for pat in pats:
    for m in re.finditer(re.escape(pat),txt): sinks.append({'type':typ,'file':rel,'line':txt[:m.start()].count('\n')+1,'pattern':pat})
 edges=[{'from_route':rt,'to_sink':sk,'confidence':'same_file'} for rt in routes for sk in sinks if rt['file']==sk['file']]
 out={'nodes':{'routes':routes,'sinks':sinks,'js_endpoints':js.get('endpoints',[]),'frontend_guards':js.get('frontend_guards',[])},'edges':edges,'policy':'regex graph is candidate graph; AST unavailable keeps needs_review'}; Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
