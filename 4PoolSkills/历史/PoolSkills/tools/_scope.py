#!/usr/bin/env python3
"""Local-only scoped file iteration and safe text helpers.

All collectors must call iter_scoped_files() rather than Path.rglob() directly.
Default policy: do not follow symlinks, never scan outside root, skip heavy dependency
caches, redact sensitive values before evidence serialization, and expose explicit
profiles so JS build artifacts can be included without globally scanning every cache.
"""
from __future__ import annotations
import hashlib, os, re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Sequence

DEFAULT_SKIP_DIRS = {
    '.git', '.hg', '.svn', 'node_modules', 'vendor', 'target', '.venv', 'venv',
    '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'coverage',
    'outputs', '.terraform', '.serverless', '.idea', '.vscode'
}
# Source scans skip generated JS artifacts. JS artifact scans intentionally do not.
SOURCE_SKIP_EXTRA = {'dist', 'build', '.next', '.nuxt', '.output', 'out', 'public/build'}
JS_ARTIFACT_ALLOWED_DIRS = {'dist', 'build', '.next', '.nuxt', '.output', 'out', 'public', 'static', 'assets'}
TEXT_EXTS = {
    '.py','.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue','.html','.htm','.json','.map',
    '.java','.kt','.php','.rb','.go','.rs','.yaml','.yml','.toml','.ini','.env','.txt',
    '.md','.graphql','.gql','.proto','.sh','.ps1','.xml','.gradle','.properties'
}
SECRET_PATTERNS = [
    (re.compile(r'(?i)(api[_-]?key|access[_-]?key|secret|token|password|passwd|jwt|private[_-]?key|client[_-]?secret)\s*[:=]\s*(["\']?)[^"\'\s]{8,}\2'), r'\1=<REDACTED>'),
    (re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----', re.S), '<REDACTED_PRIVATE_KEY>'),
    (re.compile(r'(?i)(authorization\s*:\s*bearer\s+)[A-Za-z0-9._~+/=-]{8,}'), r'\1<REDACTED>'),
]

@dataclass(frozen=True)
class ScanProfile:
    name: str = 'source'
    max_file_size: int = 2_000_000
    include_exts: frozenset[str] = field(default_factory=lambda: frozenset(TEXT_EXTS))
    skip_dirs: frozenset[str] = field(default_factory=lambda: frozenset(DEFAULT_SKIP_DIRS | SOURCE_SKIP_EXTRA))
    follow_symlinks: bool = False

PROFILES = {
    'source': ScanProfile('source'),
    'js_artifact': ScanProfile(
        'js_artifact',
        max_file_size=8_000_000,
        include_exts=frozenset({'.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue','.html','.htm','.json','.map','.wasm','.graphql','.gql'}),
        skip_dirs=frozenset(DEFAULT_SKIP_DIRS),
        follow_symlinks=False,
    ),
    'all_text': ScanProfile('all_text', max_file_size=4_000_000, skip_dirs=frozenset(DEFAULT_SKIP_DIRS), follow_symlinks=False),
}

def profile(name: str | ScanProfile = 'source') -> ScanProfile:
    if isinstance(name, ScanProfile):
        return name
    return PROFILES.get(name, PROFILES['source'])

def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False

def should_skip_dir(path: Path, root: Path, prof: ScanProfile) -> bool:
    rel_parts = path.relative_to(root).parts if path != root else ()
    parts = set(rel_parts)
    if any(part in prof.skip_dirs for part in parts):
        return True
    if prof.name == 'source' and any(part in SOURCE_SKIP_EXTRA for part in parts):
        return True
    return False

def iter_scoped_files(root: str | Path, profile_name: str | ScanProfile = 'source') -> Iterator[Path]:
    prof = profile(profile_name)
    root = Path(root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f'root_not_directory:{root}')
    for dirpath, dirnames, filenames in os.walk(root, followlinks=prof.follow_symlinks):
        d = Path(dirpath)
        if not is_relative_to(d, root) or should_skip_dir(d, root, prof):
            dirnames[:] = []
            continue
        keep=[]
        for dn in dirnames:
            dp=d/dn
            if dp.is_symlink() and not prof.follow_symlinks:
                continue
            if not should_skip_dir(dp, root, prof):
                keep.append(dn)
        dirnames[:] = keep
        for fn in filenames:
            p=d/fn
            if p.is_symlink() and not prof.follow_symlinks:
                continue
            if not p.is_file() or not is_relative_to(p, root):
                continue
            suffix=p.suffix.lower()
            if suffix and suffix not in prof.include_exts:
                continue
            try:
                if p.stat().st_size > prof.max_file_size:
                    continue
            except OSError:
                continue
            yield p

def read_text_safe(path: Path, limit: int | None = None, redact: bool = True) -> str:
    text = path.read_text(encoding='utf-8', errors='ignore')
    if limit is not None:
        text = text[:limit]
    return redact_text(text) if redact else text

def redact_text(text: str) -> str:
    for rx, repl in SECRET_PATTERNS:
        text = rx.sub(repl, text)
    return text

def sha256_file(path: str | Path) -> str:
    p=Path(path)
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def evidence_line(path: Path, root: Path, line: int, summary: str, source: str='source') -> dict:
    return {
        'id': 'ev-' + hashlib.sha256(f'{path}:{line}:{summary}'.encode()).hexdigest()[:16],
        'source': source,
        'file': str(path.relative_to(root)),
        'line': int(line or 1),
        'summary': redact_text(summary)[:500],
        'hash': sha256_file(path) if path.exists() and path.is_file() else None,
    }
