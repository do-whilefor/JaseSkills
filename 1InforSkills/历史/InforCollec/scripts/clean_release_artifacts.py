#!/usr/bin/env python3
from __future__ import annotations
import argparse
import shutil
from pathlib import Path

CACHE_DIRS = {'__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'}
STALE_FILES = {'.DS_Store', 'AUDIT_FIX_SUMMARY.md', 'CHANGELOG.md', 'RELEASE_NOTES.md'}
STALE_RELATIVE_FILES = {'docs/KEY_GAP_CLOSURE.md'}
STALE_SUFFIXES = {'.pyc', '.pyo'}


def clean(root: Path) -> dict:
    removed = []
    root = root.resolve()
    protected = {root / 'knowledge', root / 'templates'}
    for p in sorted(root.rglob('*'), key=lambda x: len(x.parts), reverse=True):
        try:
            rp = p.resolve()
        except Exception:
            rp = p
        if any(rp == q or q in rp.parents for q in protected):
            continue
        rel = str(p.relative_to(root)).replace('\\', '/')
        if p.is_dir() and p.name in CACHE_DIRS:
            shutil.rmtree(p, ignore_errors=True)
            removed.append(str(p.relative_to(root)))
        elif p.is_file() and (rel in STALE_RELATIVE_FILES or p.name in STALE_FILES or p.suffix in STALE_SUFFIXES or p.name.endswith('~')):
            try:
                p.unlink()
                removed.append(str(p.relative_to(root)))
            except FileNotFoundError:
                pass
    out = root / 'selftest' / 'out'
    if out.exists():
        shutil.rmtree(out, ignore_errors=True)
        removed.append(str(out.relative_to(root)))
    (root / 'selftest').mkdir(exist_ok=True)
    return {'status': 'PASS', 'root': str(root), 'removed': removed, 'protected': ['knowledge', 'templates']}


def main() -> int:
    ap = argparse.ArgumentParser(description='Windows-safe cleanup of generated release/test artifacts.')
    ap.add_argument('root', nargs='?', default='.')
    args = ap.parse_args()
    result = clean(Path(args.root))
    print(f"cleaned release artifacts under {result['root']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
