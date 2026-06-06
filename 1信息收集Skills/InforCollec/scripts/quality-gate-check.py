#!/usr/bin/env python3
from __future__ import annotations
import argparse
import re
from pathlib import Path

REQUIRED_SECTIONS = [
    '## A. 总览',
    '## B. 信息暴露资产表',
    '## C. 高风险发现详情',
    '## D. 中低风险发现',
    '## E. 待确认 / 不可报告',
    '## F. 反思结果',
    '## G. 下一步最小验证',
]
RAW_SECRET_HINTS = [
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----'),
    re.compile(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]{12,}\b'),
    re.compile(r'(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{16,}'),
]

def main() -> int:
    ap = argparse.ArgumentParser(description='Lightweight report quality gate checker. It does not prove correctness; it flags missing report structure and obvious raw secrets.')
    ap.add_argument('report')
    args = ap.parse_args()
    text = Path(args.report).read_text(encoding='utf-8', errors='ignore')
    ok = True
    print('# Quality Gate Check')
    for sec in REQUIRED_SECTIONS:
        if sec not in text:
            ok = False
            print(f'MISSING_SECTION\t{sec}')
    for pat in RAW_SECRET_HINTS:
        if pat.search(text):
            ok = False
            print(f'POSSIBLE_RAW_SECRET\t{pat.pattern}')
    needed_terms = ['动态证据', '不可报告原因', '复现次数', '脱敏']
    for term in needed_terms:
        if term not in text:
            ok = False
            print(f'MISSING_TERM\t{term}')
    if ok:
        print('PASS\tstructure checks passed; still manually verify evidence chain')
        return 0
    print('FAIL\treport is not ready for final delivery')
    return 1

if __name__ == '__main__':
    raise SystemExit(main())
