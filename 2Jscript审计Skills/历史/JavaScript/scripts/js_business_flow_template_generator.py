#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
FLOWS=['oauth_sso_redirect_state_code','payment_price_quota_balance_plan','approval_status_state_workflow','member_invite_permission_role','export_download_report_pdf','upload_import_parser','webhook_callback_url','template_render_preview']

def main():
    ap=argparse.ArgumentParser(description='Generate serious business-flow validation checklist templates. Templates never count as verified evidence.')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    items=[]
    for f in FLOWS:
        items.append({'flow_id':f,'status':'template-only','required_evidence':['JS callsite','API request/response','baseline vs mutated request','role diff','tenant diff','screenshot/trace/HAR','non-destructive object or dry-run mode','manual review for business impact'],'blocked_actions':['delete','real payment','external callback','bulk enumeration','approval state mutation without explicit test object']})
    res={'schema_version':'js-business-flow-templates/v1','status':'template-only','flows':items,'downgrade':'flow templates are review scaffolding; they cannot promote findings without concrete evidence.'}
    (out/'js_business_flow_templates.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'flows':len(items),'out':str(out/'js_business_flow_templates.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()
