#!/usr/bin/env python3
from __future__ import annotations
import argparse, datetime, json, sys
from pathlib import Path
import hashlib, re
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import load_scope, assert_path_allowed, read_text_scoped, redact_text, contains_unredacted_secret, sha256_file, path_decision

def now(): return datetime.datetime.now(datetime.UTC).isoformat().replace('+00:00','Z')

def _safe_evidence_filename(evidence_id: str, used: dict[str, str] | None = None, suffix: str = '.txt') -> str:
    raw = str(evidence_id or 'evidence')
    safe = re.sub(r'[^A-Za-z0-9_.-]+', '_', raw).strip('._-')
    # Windows device names are reserved even with an extension, e.g. CON.txt.
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    stem = safe.split('.', 1)[0].upper() if safe else ''
    if not safe or stem in reserved or len(safe) > 96:
        safe = 'ev-' + hashlib.sha256(raw.encode('utf-8', 'replace')).hexdigest()[:24]
    if safe.endswith(suffix):
        name = safe
    else:
        name = safe + suffix
    if used is not None:
        prior = used.get(name)
        if prior is not None and prior != raw:
            digest = hashlib.sha256(raw.encode('utf-8', 'replace')).hexdigest()[:12]
            base = safe[:72].rstrip('._-') or 'evidence'
            name = f'{base}-{digest}{suffix}'
            counter = 2
            while name in used and used[name] != raw:
                name = f'{base}-{digest}-{counter}{suffix}'
                counter += 1
        used[name] = raw
    return name

def build(root, candidates_file, scope_file=None):
    root=Path(root).resolve(); scope=load_scope(root,scope_file); cand=json.loads(Path(candidates_file).read_text(encoding='utf-8'))
    findings=cand.get('findings') or cand.get('candidates') or []
    used_evidence_filenames: dict[str, str] = {}
    raw_dir=root/(scope.get('evidence_retention_policy',{}).get('raw_dir') or 'evidence/raw')
    san_dir=root/(scope.get('evidence_retention_policy',{}).get('sanitized_dir') or 'evidence/sanitized')
    raw_dir.mkdir(parents=True,exist_ok=True); san_dir.mkdir(parents=True,exist_ok=True)
    evidence=[]
    for f in findings:
        inline=f.get('evidence_inline') or []
        if not inline and f.get('affected_files'):
            af=f['affected_files'][0]; inline=[{'evidence_id':(f.get('evidence_refs') or ['ev-'+f['finding_id']])[0],'type':'source_line','source_file':af.get('path'),'line':af.get('line'),'summary':''}]
        for ev in inline:
            src=ev.get('source_file'); eid=ev.get('evidence_id') or (f.get('evidence_refs') or ['ev'])[0]
            raw_path=san_path=None; redaction_status='clean'; h=None; scope_status='missing_source'
            content=ev.get('summary','')
            if src:
                dec=path_decision(src,root,scope); scope_status=dec.reason
                if dec.allowed and Path(dec.path).exists():
                    p=Path(dec.path); h=sha256_file(p)
                    lines=p.read_text(encoding='utf-8',errors='ignore').splitlines(); ln=int(ev.get('line') or 1)
                    start=max(0,ln-3); stop=min(len(lines),ln+2); content='\n'.join(f'{i+1}: {lines[i]}' for i in range(start,stop))
            redacted,redaction_status=redact_text(content)
            safe_name=_safe_evidence_filename(eid, used_evidence_filenames)
            raw_file=raw_dir/safe_name; san_file=san_dir/safe_name
            raw_file.write_text(content,encoding='utf-8'); san_file.write_text(redacted,encoding='utf-8')
            evidence.append({'evidence_id':eid,'type':ev.get('type','source_line'),'source_file':src,'source_tool':'evidence_manifest_builder','command':'local_source_extract','timestamp':now(),'hash':h,'scope_status':scope_status,'redaction_status':'failed_unredacted_secret' if contains_unredacted_secret(redacted) else redaction_status,'raw_path':str(raw_file.relative_to(root)),'sanitized_path':str(san_file.relative_to(root)),'related_finding':f.get('finding_id') or f.get('id'),'related_route':None,'related_role':None,'related_tenant':None,'request_ref':None,'response_ref':None,'screenshot_ref':None,'trace_ref':None,'har_ref':None,'console_ref':None,'dom_ref':None})
    return {'schema_version':'evidence-manifest-v1','generated_at':now(),'root':str(root),'policy':{'raw_and_sanitized_separated':True,'reports_may_reference_raw':False},'evidence':evidence,'summary':{'evidence':len(evidence),'redaction_failures':sum(1 for e in evidence if e['redaction_status']=='failed_unredacted_secret')}}
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True); ap.add_argument('--candidates',required=True); ap.add_argument('--scope-file'); ap.add_argument('--out',required=True); ns=ap.parse_args(); data=build(ns.root,ns.candidates,ns.scope_file); Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps(data['summary'],ensure_ascii=False))
if __name__=='__main__': main()
