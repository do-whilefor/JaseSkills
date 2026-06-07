#!/usr/bin/env python3
import json, sys
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'config/authorized_targets.json').read_text(encoding='utf-8'))
DESTRUCTIVE={'DELETE','PURGE'}; STATE_CHANGING={'POST','PUT','PATCH'}
def check(method, url, dry_run=True):
    method=method.upper(); u=urlparse(url); host=u.hostname or ''
    reasons=[]
    if not (host in CFG.get('authorized_hosts',[]) or host.endswith('.localhost') or u.scheme=='file'): reasons.append('target_not_authorized_local_scope')
    if u.scheme not in CFG.get('allowed_schemes',['http','https','file']): reasons.append('scheme_not_allowed')
    if method in DESTRUCTIVE: reasons.append('destructive_method_blocked')
    if method in STATE_CHANGING and not dry_run: reasons.append('state_changing_method_requires_explicit_safe_fixture')
    return {'status':'allow' if not reasons else 'block','method':method,'url':url,'dry_run':dry_run,'reasons':reasons,'policy':'local-authorized non-destructive only'}
if __name__=='__main__':
    out=check(sys.argv[1] if len(sys.argv)>1 else 'GET', sys.argv[2] if len(sys.argv)>2 else 'http://127.0.0.1/', '--execute' not in sys.argv)
    print(json.dumps(out,ensure_ascii=False,indent=2)); raise SystemExit(0 if out['status']=='allow' else 2)
