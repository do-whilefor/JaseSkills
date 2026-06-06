#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import re
import sys

PATTERNS = [
    (re.compile(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b'), 'JWT'),
    (re.compile(r'\bsk_live_[A-Za-z0-9]{8,}\b'), 'API_KEY'),
    (re.compile(r'(?i)(mysql|postgres|postgresql|mongodb|redis)://([^\s"\']+)'), 'DB_URL'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----'), 'PRIVATE_KEY'),
    (re.compile(r'(?i)(password|secret|token|api[_-]?key|client[_-]?secret)\s*[:=]\s*["\']?([^\s"\',}]{8,})'), 'KV_SECRET'),
]

def mask_value(value: str, kind: str) -> str:
    digest = hashlib.sha256(value.encode('utf-8', errors='ignore')).hexdigest()[:16]
    if kind == 'JWT':
        return f'eyJ****.****.****; 长度:{len(value)}; SHA256:{digest}'
    if kind == 'DB_URL':
        return f'{value.split("://",1)[0]}://****; 长度:{len(value)}; SHA256:{digest}'
    if kind == 'PRIVATE_KEY':
        return f'类型:Private Key; 长度:{len(value)}; SHA256:{digest}'
    if len(value) <= 12:
        return f'****; 长度:{len(value)}; SHA256:{digest}'
    return f'{value[:6]}****{value[-4:]}; 长度:{len(value)}; SHA256:{digest}'

def redact(text: str) -> str:
    out = text
    for pattern, kind in PATTERNS:
        if kind == 'KV_SECRET':
            out = pattern.sub(lambda m: f'{m.group(1)}={mask_value(m.group(2), kind)}', out)
        else:
            out = pattern.sub(lambda m: mask_value(m.group(0), kind), out)
    return out

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('file', nargs='?')
    args = ap.parse_args()
    if args.file:
        with open(args.file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    else:
        text = sys.stdin.read()
    print(redact(text), end='')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
