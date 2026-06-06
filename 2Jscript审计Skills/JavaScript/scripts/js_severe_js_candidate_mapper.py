#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

RULES=[
 ('authz-bypass','权限绕过 / 前端权限控制后端未校验', re.compile(r'(role|permission|isAdmin|admin)', re.I)),
 ('idor','IDOR / 越权访问', re.compile(r'(userId|ownerId|accountId|projectId|fileId|\bid\b)', re.I)),
 ('tenant-bypass','租户隔离绕过', re.compile(r'(tenantId|orgId|workspaceId|companyId)', re.I)),
 ('mass-assignment','Mass Assignment / Over-posting', re.compile(r'(role|isAdmin|status|state|price|quota|plan|balance|approved|override|force)', re.I)),
 ('graphql-authz','GraphQL 字段或 mutation 越权', re.compile(r'(graphql|mutation|query|variables)', re.I)),
 ('websocket-authz','WebSocket 隐藏 action 越权', re.compile(r'(websocket|action|event|type)', re.I)),
 ('ssrf-open-redirect','SSRF / Open Redirect / callback 注入', re.compile(r'(url|uri|redirect|redirect_uri|callback|webhook)', re.I)),
 ('file-read-write','任意文件读写/下载/上传入口', re.compile(r'(file|filename|path|upload|download|export|template)', re.I)),
 ('debug-danger','debug/dryRun/force/override 危险路径', re.compile(r'(debug|dryRun|force|override)', re.I)),
]

def load(p:Path, default):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default

def uniq(xs):
    out=[]
    for x in xs:
        if x and x not in out: out.append(x)
    return out

def main():
    ap=argparse.ArgumentParser(description='Map JS API/hidden parameter candidates to severe vulnerability validation chains')
    ap.add_argument('--api-model', required=True)
    ap.add_argument('--param-diff', default='')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    model=load(Path(args.api_model), {})
    diff=load(Path(args.param_diff), {}) if args.param_diff else {}
    candidates=[]; idx=1
    diff_fields=diff.get('high_risk_hidden_or_backend_only_fields', [])
    for api in model.get('apis', []):
        fields=uniq(api.get('high_risk_params',[])+api.get('hidden_param_candidates',[])+api.get('query_params',[])+api.get('body_params',[])+api.get('graphql_variables',[])+api.get('websocket_message_types',[])+diff_fields)
        hay=' '.join([api.get('protocol',''), api.get('path',''), api.get('graphql_operationName') or '', api.get('json_rpc_method') or ''] + fields)
        for rule_id,title,rgx in RULES:
            if rgx.search(hay):
                candidates.append({'candidate_id':f'SEVERE-CAND-{idx:04d}','vulnerability_type':title,'rule_id':rule_id,'status':'candidate-only','api':{'protocol':api.get('protocol'),'method':api.get('method'),'path':api.get('path'),'call_file':api.get('call_file'),'line':api.get('line')},'parameters':fields,'js_evidence':api.get('evidence',[]),'trigger_page':api.get('route_page','unknown'),'trigger_action':api.get('trigger_condition','unknown'),'role_requirement':'unknown until replay','tenant_requirement':'unknown until replay','risk_reason':'High-risk endpoint/parameter pattern from JS/API/backend diff; not proof of exploitability','non_destructive_validation':['compare UI request vs direct API request with one extra parameter','normal user vs admin','tenant A object vs tenant B object','owned object vs unowned object','expect no state change unless using test object and rollback plan'],'expected_response_difference':['403/401 expected for unauthorized role/tenant','no sensitive fields should be returned by include/expand/fields','extra backend-only field must be ignored or rejected'],'false_positive_risk':'high until request/response evidence exists','human_review_required':True,'fix_suggestion':'Enforce server-side authorization, allowlist request DTO fields, reject unknown sensitive fields, bind tenant/object ownership server-side'})
                idx+=1
    result={'schema_version':'js-severe-candidate-map/v1','status':'partial' if candidates else 'empty','candidates':candidates,'downgrade':'All entries are candidate-only until dynamic role/tenant replay evidence exists'}
    (out/'js_severe_candidate_map.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'out':str(out/'js_severe_candidate_map.json'),'candidates':len(candidates)}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()
