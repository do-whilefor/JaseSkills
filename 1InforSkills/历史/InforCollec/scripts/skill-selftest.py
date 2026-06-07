#!/usr/bin/env python3
"""Self-test SKILL.md files for required operational sections.

This is a structure checker, not a semantic proof. It helps prevent accidental
loss of trigger rules, inputs, steps, outputs, failure handling, quality gates,
and extension markers during maintenance.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

REQUIRED = {
    'one_line_purpose': [r'^#\s+', r'解决|用于|负责|用途'],
    'must_call': [r'必须调用|触发场景|什么时候必须'],
    'forbidden': [r'禁止调用|不得调用|禁止'],
    'inputs': [r'输入|输入材料'],
    'steps': [r'执行步骤|处理流程|流程|步骤'],
    'outputs': [r'输出|产出'],
    'checkpoints': [r'检查点|验收|质量门槛|质量'],
    'failure_handling': [r'失败处理|失败|不可报告|待确认|不可交付'],
    'collaboration': [r'协作|交接|回流|调用.*Skill|上游|下游'],
    'anti_injection': [r'prompt injection|注入|README|注释|测试数据|源码.*规则'],
    'traceability': [r'证据|可追溯|动态验证|来源|映射'],
    'extension_marker': [r'基于文档延伸|延伸']
}


def check_file(path: Path) -> dict:
    text = path.read_text(encoding='utf-8', errors='ignore')
    results = {}
    for key, pats in REQUIRED.items():
        results[key] = any(re.search(p, text, re.I | re.M) for p in pats)
    score = sum(1 for ok in results.values() if ok)
    return {
        'path': str(path),
        'score': score,
        'max_score': len(REQUIRED),
        'status': 'PASS' if score == len(REQUIRED) else 'FAIL',
        'missing': [k for k,v in results.items() if not v]
    }


def main() -> int:
    ap = argparse.ArgumentParser(description='Check SKILL.md structural completeness.')
    ap.add_argument('root', nargs='?', default='.', help='Skills root directory')
    ap.add_argument('--out', default=None, help='Write JSON report')
    args = ap.parse_args()
    root = Path(args.root)
    files = sorted(root.rglob('SKILL.md'))
    report = {'root': str(root), 'skill_count': len(files), 'results': [check_file(p) for p in files]}
    report['overall_status'] = 'PASS' if files and all(r['status']=='PASS' for r in report['results']) else 'FAIL'
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding='utf-8')
    print(text)
    return 0 if report['overall_status'] == 'PASS' else 2

if __name__ == '__main__':
    raise SystemExit(main())
