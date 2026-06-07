#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def h(x): return hashlib.sha256(str(x).encode()).hexdigest()[:16]
def convert(har_path, out_path=None):
    p=Path(har_path); data=json.loads(p.read_text(encoding='utf-8')); entries=data.get('log',{}).get('entries',[]); candidates=[]
    for idx,e in enumerate(entries):
        req=e.get('request',{}); resp=e.get('response',{}); url=req.get('url',''); method=req.get('method','GET')
        cid='har-'+h(method+url+str(idx))
        candidates.append({'id':cid,'type':'dynamic_observation','severity':'info','status':'needs_review','source':'har','route':url,'method':method,'parameter':None,'auth_context':{},'tenant_context':{},'role_matrix':[],'tenant_matrix':[],
          'code_evidence':[], 'js_evidence':[],
          'dynamic_evidence':[{'id':cid+'-dyn','source':'har','route':url,'method':method,'request':{'url':url,'headers_count':len(req.get('headers',[]))},'response':{'status':resp.get('status'),'mimeType':resp.get('content',{}).get('mimeType')},'har_path':str(p),'summary':'HAR request/response observation; not a vulnerability by itself'}],
          'negative_controls':[], 'state_history':[{'from':None,'to':'triaged','reason':'imported from HAR as observation only','timestamp':datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')}],
          'impact_proof':{}, 'false_positive_exclusions':['HAR import is not evidence of exploitability'], 'quality_gate':{'score':0,'status':'needs_review','hard_failures':['missing_code_evidence','missing_negative_controls']}, 'report_mapping':{}, 'non_destructive':{'is_non_destructive':True,'data_modified':False,'boundary':'HAR import only'}})
    out={'manifest_version':'4.0','generated_at':datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z'),'scope':{'mode':'local_authorized','project_root':str(ROOT),'allowed_hosts':['127.0.0.1','localhost'],'forbidden_actions':['destructive_state_change','dos','third_party_targeting']},'candidates':candidates}
    outp=Path(out_path) if out_path else ROOT/'outputs/har_evidence_manifest_v4.json'
    if not outp.is_absolute(): outp=ROOT/outp
    outp.parent.mkdir(parents=True,exist_ok=True); outp.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'ok','output':str(outp),'candidates':len(candidates),'manifest_version':'4.0'},ensure_ascii=False,indent=2))
    return outp
if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('har', nargs='?', default=str(ROOT/'tests/fixtures/sample.har')); ap.add_argument('--out', default=None); a=ap.parse_args(); convert(a.har,a.out)
