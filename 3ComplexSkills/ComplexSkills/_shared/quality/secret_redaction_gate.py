#!/usr/bin/env python3
"""Second-pass secret redaction gate for generated audit outputs.
Scans provided output paths with bounded line scanning to avoid regex DoS on large JSON artifacts.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
PATTERNS=[
 ('aws_access_key', re.compile(r'AKIA[0-9A-Z]{16}')),
 ('private_key', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----')),
 ('github_pat', re.compile(r'gh[pousr]_[A-Za-z0-9_]{30,}')),
 ('slack_token', re.compile(r'xox[baprs]-[A-Za-z0-9-]{20,}')),
 ('jwt', re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}')),
 ('generic_secret_assignment', re.compile(r'(?i)(secret|token|password|api[_-]?key)\s*[:=]\s*["\']?[A-Za-z0-9_./+=-]{20,80}')),
]
SKIP_SUFFIX={'.png','.jpg','.jpeg','.gif','.webp','.zip','.gz','.tgz','.ico','.pdf','.sqlite','.db'}
SKIP_DIRS={'.git','node_modules','vendor','__pycache__'}
MAX_FILE_BYTES=8_000_000
MAX_LINE_CHARS=4000
MAX_FINDINGS=200

def iter_paths(p: Path):
    if p.is_file():
        yield p
    elif p.exists():
        for x in p.rglob('*'):
            if x.is_file(): yield x

def scan_file(f: Path, findings: list[dict]) -> bool:
    if any(part in SKIP_DIRS for part in f.parts) or f.suffix.lower() in SKIP_SUFFIX:
        return False
    try:
        if f.stat().st_size > MAX_FILE_BYTES:
            findings.append({'path':str(f),'type':'scan_skipped_large_file','offset':0,'preview':'<large-file>','policy':'large generated file must be scanned separately before release'})
            return True
    except Exception:
        return False
    try:
        with f.open('r', encoding='utf-8', errors='ignore') as fh:
            offset=0
            for line in fh:
                chunk=line[:MAX_LINE_CHARS]
                for name,rx in PATTERNS:
                    for m in rx.finditer(chunk):
                        findings.append({'path':str(f),'type':name,'offset':offset+m.start(),'preview':m.group(0)[:12]+'...','policy':'raw secret-like value must be redacted before reporting'})
                        if len(findings)>=MAX_FINDINGS: return True
                offset += len(line)
    except Exception:
        return False
    return True

def scan_path(p: Path):
    findings=[]; count=0
    for f in iter_paths(p):
        if scan_file(f, findings): count += 1
        if len(findings)>=MAX_FINDINGS: break
    return count, findings

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('paths', nargs='+'); ap.add_argument('--out')
    a=ap.parse_args(); total=0; findings=[]
    for s in a.paths:
        c,fs=scan_path(Path(s)); total += c; findings.extend(fs)
        if len(findings)>=MAX_FINDINGS: break
    res={'schema_version':'secret_redaction_gate_v2','scanned_path_count':total,'finding_count':len(findings),'passed':len(findings)==0,'findings':findings[:MAX_FINDINGS],'scanner_limits':{'max_file_bytes':MAX_FILE_BYTES,'max_line_chars':MAX_LINE_CHARS}}
    text=json.dumps(res,ensure_ascii=False,indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(text+'\n',encoding='utf-8')
    print(text); return 0 if res['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
