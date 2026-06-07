#!/usr/bin/env python3
import argparse,json,subprocess,sys
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--cases',default='tests/regression_cases.json'); ap.add_argument('--out',default='outputs/regression_results.json'); a=ap.parse_args(); r=Path(a.root); cases=json.loads((r/a.cases).read_text(encoding='utf-8'))['cases']; res=[]
 for c in cases:
  ok=all(k in c for k in ['id','type','input','expected_skill','expected_status']); notes=[]
  if c.get('fixture'):
   p=subprocess.run([sys.executable,str(r/'scripts/quality_gate_score.py'),str(r/c['fixture']),'--out',str(r/'outputs'/('q_'+c['id']+'.json'))],cwd=str(r),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
   q=json.loads((r/'outputs'/('q_'+c['id']+'.json')).read_text(encoding='utf-8'))[0]
   ok=ok and q.get('allowed_status')==c.get('expected_allowed_status'); notes.append('allowed='+q.get('allowed_status',''))
  res.append({'id':c['id'],'ok':ok,'notes':notes})
 out=r/a.out; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(res,ensure_ascii=False,indent=2)); sys.exit(0 if all(x['ok'] for x in res) else 2)
if __name__=='__main__': main()
