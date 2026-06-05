#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
SENSITIVE_RE=re.compile(r'(token|secret|api[_-]?key|password|private[_-]?key|session|cookie|database[_-]?url|jwt)',re.I)
SECRET_PATTERNS=[re.compile(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b'),re.compile(r'\bsk_live_[A-Za-z0-9]{8,}\b'),re.compile(r'(?i)(mysql|postgres|postgresql|mongodb|redis)://([^\s"\']+)'),re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----'),re.compile(r'(?i)((password|secret|token|api[_-]?key|client[_-]?secret)\s*[:=]\s*["\']?)([^\s"\',}]{8,})')]
SKIP_DIRS={'.git','node_modules','vendor','.venv','venv','__pycache__','.next/cache','target'}
def mask(value:str)->str:
    h=hashlib.sha256(value.encode('utf-8',errors='ignore')).hexdigest()[:16]
    return f'****;长度:{len(value)};SHA256:{h}' if len(value)<=12 else f'{value[:4]}****{value[-4:]};长度:{len(value)};SHA256:{h}'
def redact(text:str)->str:
    out=text
    for pat in SECRET_PATTERNS:
        if pat.pattern.startswith('(?i)(('): out=pat.sub(lambda m:m.group(1)+mask(m.group(3)),out)
        else: out=pat.sub(lambda m:mask(m.group(0)),out)
    return out
def should_skip(p:Path)->bool: return any(part in SKIP_DIRS for part in p.parts)
def summarize_file(path:Path,max_bytes:int)->dict:
    data=path.read_bytes(); text=data[:max_bytes].decode('utf-8',errors='ignore'); keys=sorted(set(m.group(1).lower() for m in SENSITIVE_RE.finditer(text)))
    return {'file':str(path),'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'possible_sensitive_names':keys,'preview_redacted':redact(text[:500]).replace('\n','\\n')}
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('paths',nargs='+'); ap.add_argument('-o','--output',default='response-summary.json'); ap.add_argument('--max-files',type=int,default=1000); ap.add_argument('--max-bytes',type=int,default=20000)
    args=ap.parse_args(); results=[]
    for item in args.paths:
        p=Path(item)
        if p.is_dir():
            for f in p.rglob('*'):
                if len(results)>=args.max_files: break
                if f.is_file() and not should_skip(f):
                    try: results.append(summarize_file(f,args.max_bytes))
                    except Exception: pass
        elif p.is_file() and not should_skip(p): results.append(summarize_file(p,args.max_bytes))
    Path(args.output).write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8'); print(f'wrote {len(results)} summaries to {args.output}'); return 0
if __name__=='__main__': raise SystemExit(main())
