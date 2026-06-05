#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path

def run_step(name: str, cmd: list[str], root: Path, outdir: Path, timeout: int) -> dict:
    logs = outdir / 'logs'; logs.mkdir(parents=True, exist_ok=True)
    (logs / f'{name}.cmd.json').write_text(json.dumps(cmd, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'[selftest] start {name}', flush=True)
    proc = subprocess.run(cmd, cwd=root, text=True, capture_output=True, timeout=timeout)
    (logs / f'{name}.stdout').write_text(proc.stdout or '', encoding='utf-8')
    (logs / f'{name}.stderr').write_text(proc.stderr or '', encoding='utf-8')
    status = 'PASS' if proc.returncode == 0 else 'FAIL'
    print(f'[selftest] done {name} {status}', flush=True)
    return {'name': name, 'status': status, 'returncode': proc.returncode, 'cmd': cmd}

def main() -> int:
    ap = argparse.ArgumentParser(description='Run stable package selftest for the clean Skills package.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--outdir', default='selftest/out')
    ap.add_argument('--timeout', type=int, default=30)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    out = Path(args.outdir).resolve(); out.mkdir(parents=True, exist_ok=True)
    def p(x: str) -> str: return str(root / x)
    def o(x: str) -> str: return str(out / x)
    steps = [
        ('skill-selftest', ['python3', p('scripts/skill-selftest.py'), str(root), '--out', o('skill-selftest.json')]),
        ('parser-backend-check', ['python3', p('scripts/parser-backend-check.py'), '--out', o('parser-backend-check.json')]),
        ('runtime-readiness-check', ['python3', p('scripts/runtime-readiness-check.py'), '--project-root', str(root), '--out', o('runtime-readiness-check.json')]),
        ('js-asset-audit', ['python3', p('scripts/js-asset-audit.py'), p('tests/fixtures/js_app'), '-o', o('js-fixture-candidates.jsonl')]),
        ('code-surface', ['python3', p('scripts/code-surface-inventory.py'), p('tests/fixtures/python_app'), '-o', o('code-surface-fixture.jsonl')]),
        ('manifest-index-tests', ['python3', '-m', 'pytest', '-q', p('tests/test_manifest_indexes.py'), p('tests/test_all_templates_indexed.py'), p('tests/test_stale_reference_gate.py')]),
    ]
    results=[]
    for name, cmd in steps:
        try:
            result = run_step(name, cmd, root, out, args.timeout)
        except subprocess.TimeoutExpired as exc:
            result = {'name': name, 'status': 'TIMEOUT', 'returncode': 124, 'cmd': cmd, 'error': str(exc)}
            print(f'[selftest] done {name} TIMEOUT', flush=True)
        results.append(result)
        if result['status'] != 'PASS':
            (out/'selftest-summary.json').write_text(json.dumps({'status':'FAIL','results':results}, ensure_ascii=False, indent=2), encoding='utf-8')
            return int(result.get('returncode') or 1) or 1
    (out/'selftest-summary.json').write_text(json.dumps({'status':'PASS','results':results}, ensure_ascii=False, indent=2), encoding='utf-8')
    (out/'SELFTEST_COMPLETED.txt').write_text('Selftest completed\n', encoding='utf-8')
    print(f'Selftest completed: {out}', flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
