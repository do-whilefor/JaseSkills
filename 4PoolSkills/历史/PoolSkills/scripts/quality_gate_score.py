#!/usr/bin/env python3
import argparse,json
from pathlib import Path
from evidence_manifest_validate import validate_item
def score_item(x):
    err=validate_item(x)['errors']; score=0; miss=[]
    for k,pts in [('code_evidence',20),('dynamic_evidence',20),('impact',15),('false_positive_notes',5)]:
        if x.get(k): score+=pts
        else: miss.append(k)
    if x.get('negative_control',{}).get('performed') is True: score+=15
    else: miss.append('negative_control')
    if int(x.get('reproduction_count') or 0)>=3 and len(x.get('reproduction_attempts') or [])>=3: score+=10
    else: miss.append('3x_reproduction')
    if x.get('auth_context',{}).get('login_state')!='unknown' and x.get('tenant_context',{}).get('comparison')!='unknown': score+=10
    else: miss.append('auth_tenant_context')
    if x.get('non_destructive',{}).get('is_non_destructive') is True and x.get('non_destructive',{}).get('data_modified') is False: score+=5
    else: miss.append('non_destructive')
    if any(e in err for e in ['scope_not_authorized','destructive_or_modified']): status='blocked'
    elif err or score<80: status='needs_review'
    else: status='confirmed'
    return {'candidate_id':x.get('candidate_id','unknown'),'score':score,'missing':miss,'validation_errors':err,'declared_status':x.get('final_status','candidate'),'allowed_status':status}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('manifest'); ap.add_argument('--out',default='outputs/quality_results.json'); a=ap.parse_args(); d=json.loads(Path(a.manifest).read_text(encoding='utf-8')); items=d if isinstance(d,list) else d.get('items',[d]); res=[score_item(i) for i in items]; Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(res,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
