#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,datetime,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts'))
from _scope import iter_scoped_files, read_text_safe
REG=json.loads((Path(__file__).resolve().parent/'registry.json').read_text(encoding='utf-8'))
PATTERNS={
 'authentication_bypass':[r'permitAll\s*\(',r'auth\s*:\s*false',r'public\s*:\s*true',r'skipAuth',r'AllowAnonymous',r'withoutMiddleware\(["\']auth'],
 'authorization_bypass':[r'admin',r'permission',r'authorize',r'can\(',r'policy',r'@Roles',r'isOwner'],
 'idor_bola':[r'params\.(id|userId|projectId|orgId)',r'PathVariable.*(id|userId|projectId)',r'find(ById|Unique|First)',r'req\.query\.(id|userId|projectId)'],
 'tenant_isolation_bypass':[r'tenant(Id)?',r'org(Id)?',r'workspace(Id)?',r'x-tenant',r'subdomain'],
 'admin_privilege_escalation':[r'isAdmin|role|roles|permissions',r'mass.?assign|fillable|guarded',r'update\(.*role'],
 'rce':[r'eval\s*\(',r'new Function\s*\(',r'Runtime\.getRuntime\(\)\.exec',r'ProcessBuilder',r'vm\.runIn'],
 'command_injection':[r'exec\s*\(',r'spawn\s*\(',r'system\s*\(',r'shell_exec',r'Command::new'],
 'ssti':[r'render_template_string|Template\(|from_string|Freemarker|Velocity|Twig'],
 'deserialization':[r'pickle\.loads|yaml\.load|ObjectInputStream|unserialize\s*\(|Marshal\.load'],
 'arbitrary_file_read':[r'readFile|read_file|File\.read|open\s*\(|Files\.read|sendFile'],
 'arbitrary_file_write':[r'writeFile|write_file|File\.write|Files\.write|fopen|move_uploaded_file'],
 'file_upload_rce_or_overwrite':[r'multer|multipart|upload|move_uploaded_file|ActiveStorage|fileUpload'],
 'ssrf':[r'fetch\s*\(|axios\.|requests\.get|http\.Get|RestTemplate|open-uri|imageProxy|webhook'],
 'sql_injection':[r'raw\(|query\s*\(|execute\s*\(|createNativeQuery|\$queryRaw|whereRaw'],
 'nosql_injection':[r'find\(|findOne\(|aggregate\(|\$where|mongo|mongoose'],
 'orm_raw_query_injection':[r'raw\(|queryRaw|executeRaw|createNativeQuery|whereRaw|DB::raw'],
 'graphql_authz_batch_introspection':[r'GraphQL|resolver|introspection|gql`|subscription'],
 'webhook_signature_bypass':[r'webhook|signature|hmac|x-hub-signature|stripe-signature'],
 'jwt_token_validation':[r'jwt|jsonwebtoken|verify\(|decode\(|alg.*none'],
 'oauth_sso_redirect':[r'oauth|saml|redirect_uri|callback|nonce|state'],
 'cors_misconfiguration':[r'Access-Control-Allow-Origin|cors\(|credentials.*true'],
 'sensitive_info_disclosure':[r'secret|token|api[_-]?key|password|SENTRY_DSN|SUPABASE|FIREBASE'],
 'business_logic_high_impact':[r'invite|approval|discount|price|quota|refund|transfer|workflow|state'],
 'supply_chain_dependency_plugin':[r'postinstall|preinstall|plugin|require\(|import\(|loadPlugin|build.rs'],
 'cache_key_confusion':[r'cacheKey|Vary|CDN|stale-while-revalidate|revalidate|Cache-Control'],
 'graphql_authz_bypass':[r'GraphQL|resolver|fragment|introspection|@Authorized|context\.user'],
 'websocket_authz_bypass':[r'WebSocket|socket\.io|onmessage|messageType|subscribe|channel'],
 'cicd_secret_supply_chain':[r'github\.com/workflows|secrets\.|GITHUB_TOKEN|CI_|postinstall|preinstall|docker build'],
 'debug_internal_admin_exposure':[r'debug|trace|devMode|staging|internal|admin|swagger|actuator'],
 'state_machine_bypass':[r'status|state|workflow|approval|step|transition|draft|publish'],
 'mass_assignment':[r'Object\.assign|\.update\(|fill\(|fillable|guarded|spread|\.merge\(|patch'],
 'http_parameter_pollution':[r'req\.query|request\.GET|QueryDict|getlist|URLSearchParams|params\.append'],
 'ssrf_metadata_internal':[r'169\.254\.169\.254|metadata|localhost|127\.0\.0\.1|internal|webhook|callback'],
 'import_export_data_authz':[r'import|export|csv|xlsx|report|download|bulk'],
 'report_search_filter_authz':[r'search|filter|sort|orderBy|page|limit|cursor|report'],
 'soft_delete_history_draft_authz':[r'softDelete|deleted_at|trash|archive|history|version|draft'],
 'org_workspace_switch_bypass':[r'orgId|organizationId|workspaceId|teamId|projectId|spaceId|tenantId'],
 'invite_share_magic_reset_logic':[r'invite|share|magic|reset|verify|token|link|expiry'],
 'pricing_order_coupon_balance_logic':[r'price|coupon|discount|order|balance|credit|points|subscription|plan']
}

def h(x): return hashlib.sha256(x.encode()).hexdigest()[:12]
def now(): return datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')

def scan(project):
    root=Path(project).resolve(); candidates=[]
    for p in iter_scoped_files(root,'all_text'):
        try: txt=read_text_safe(p, limit=500000, redact=True)
        except Exception: continue
        rel=str(p.relative_to(root))
        for det in REG['detectors']:
            pats=PATTERNS.get(det['type'],[]); hits=[]
            for rx in pats:
                m=re.search(rx, txt, re.I)
                if m: hits.append({'pattern':rx,'line':txt[:m.start()].count('\n')+1,'excerpt':m.group(0)[:80]})
            if hits:
                cid='cand-'+h(det['type']+rel+str(hits[0]['line']))
                candidates.append({'id':cid,'type':det['type'],'severity':'unknown','status':'needs_review','source':'detector','reachability_status':'static_signal_only_no_source_sink_proof','route':None,'method':None,'parameter':None,'auth_context':{},'tenant_context':{},'role_matrix':[],'tenant_matrix':[],'code_evidence':[{'id':cid+'-code','source':'detector','file':rel,'line':hits[0]['line'],'summary':'Static signal only: '+', '.join(sorted({x['excerpt'] for x in hits})[:3])}], 'js_evidence':[], 'dynamic_evidence':[], 'negative_controls':[], 'dynamic_state':'STATIC_CANDIDATE','state_history':[{'from':None,'to':'triaged','reason':'static detector candidate; requires graph, dynamic evidence and negative controls','timestamp':now()}], 'impact_proof':{}, 'false_positive_exclusions':det.get('required_negative_controls',[]), 'quality_gate':{'score':20,'status':'needs_review','hard_failures':['missing_dynamic_evidence','missing_negative_controls','static_candidate_only']}, 'report_mapping':{'template':'vulnerability_templates/'+det['id']+'.md','report_template':'report_templates/'+det['id']+'.report.md'}, 'information_collection_links':['asset-ledger-v2','route-inventory-v1','auth-graph-v1'], 'js_audit_links':['js-asset-v1','js-audit-graph-v1'], 'non_destructive':{'is_non_destructive':True,'data_modified':False,'boundary':'static local scan only'}})
    return candidates

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--out',default=str(ROOT/'outputs/detector_candidates_v4.json')); a=ap.parse_args()
    candidates=scan(a.project)
    manifest={'manifest_version':'4.0','generated_at':now(),'scope':{'mode':'local_authorized','project_root':str(Path(a.project).resolve()),'allowed_hosts':['127.0.0.1','localhost'],'forbidden_actions':['destructive_state_change','dos','third_party_targeting']},'candidates':candidates}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'status':'ok','candidates':len(candidates),'output':a.out,'policy':REG['policy']},ensure_ascii=False,indent=2))
if __name__=='__main__': main()
