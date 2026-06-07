#!/usr/bin/env python3
"""Redact and hash local HAR files into Skill-root relative evidence artifacts."""
from __future__ import annotations
import argparse, json, hashlib, re
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[3]
SECRET_RE = re.compile(r'(authorization|cookie|token|secret|api[-_]?key|password)', re.I)
def sha_file(p: Path) -> str:
    h=hashlib.sha256();
    with p.open('rb') as f:
        for b in iter(lambda:f.read(65536), b''): h.update(b)
    return h.hexdigest()
def rel(p: Path) -> str: return str(p.resolve().relative_to(ROOT))
def redact(o: Any) -> Any:
    if isinstance(o, dict):
        return {k: ('<redacted>' if SECRET_RE.search(str(k)) else redact(v)) for k,v in o.items()}
    if isinstance(o, list): return [redact(x) for x in o]
    if isinstance(o, str) and SECRET_RE.search(o): return '<redacted-string>'
    return o
def convert(har: Path, out_dir: Path, run_id: str) -> list[dict[str,Any]]:
    obj=json.loads(har.read_text(encoding='utf-8'))
    entries=(obj.get('log') or {}).get('entries') or []
    out=[]; art_dir=out_dir / run_id / 'artifacts'; art_dir.mkdir(parents=True, exist_ok=True)
    for i,e in enumerate(entries):
        case=f'{run_id}-har-{i:03d}'; req=redact(e.get('request') or {}); resp=redact(e.get('response') or {})
        req_p=art_dir/f'{case}_request.json'; resp_p=art_dir/f'{case}_response.json'
        req_p.write_text(json.dumps(req,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); resp_p.write_text(json.dumps(resp,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        out.append({'case_id':case,'non_destructive':True,'source':'har_redaction_and_hash','artifacts':[{'type':'request','path':rel(req_p),'sha256':sha_file(req_p),'redacted':True},{'type':'response','path':rel(resp_p),'sha256':sha_file(resp_p),'redacted':True}]})
    return out
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('har'); ap.add_argument('--run-id',default='local-run'); ap.add_argument('--out-dir',default=str(ROOT/'_shared/runs')); ap.add_argument('--out')
    a=ap.parse_args(); res=convert(Path(a.har), Path(a.out_dir), a.run_id); text=json.dumps({'schema_version':'dynamic_evidence_groups_v1','groups':res},ensure_ascii=False,indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(text+'\n',encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()
