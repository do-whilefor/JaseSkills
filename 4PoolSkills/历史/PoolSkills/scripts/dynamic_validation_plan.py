#!/usr/bin/env python3
import argparse,json
from pathlib import Path
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('candidates'); ap.add_argument('--out',default='outputs/dynamic_validation_plan.json'); a=ap.parse_args(); d=json.loads(Path(a.candidates).read_text(encoding='utf-8')); items=d if isinstance(d,list) else d.get('items',[d]); plans=[]
 for c in items: plans.append({'candidate_id':c.get('candidate_id','unknown'),'route':c.get('route',''),'method':c.get('method',''),'parameter':c.get('parameter',''),'contexts':['unauthenticated','ordinary_user','comparison_user','admin','same_tenant','cross_tenant'],'required_evidence':['code','request_response','negative_control','3x_reproduction','impact'],'blocked_actions':['third-party','MITM','DoS','credential spraying','real data deletion'],'non_destructive_strategy':'read-only or test canary only'})
 out={'plans':plans}; Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
