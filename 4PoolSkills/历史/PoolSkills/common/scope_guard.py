#!/usr/bin/env python3
from __future__ import annotations
import hashlib, ipaddress, os, re, socket
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Any
from urllib.parse import urlparse
try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

DEFAULT_TEXT_EXTS = {
    '.py','.js','.jsx','.ts','.tsx','.mjs','.cjs','.vue','.html','.htm','.json','.map',
    '.java','.kt','.php','.rb','.go','.rs','.yaml','.yml','.toml','.ini','.env','.txt',
    '.md','.graphql','.gql','.proto','.sh','.ps1','.xml','.gradle','.properties','.tf','.hcl'
}
SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_-]?key|access[_-]?key|secret|token|password|passwd|jwt|private[_-]?key|client[_-]?secret)\s*[:=]\s*(["\']?)[^"\'\s]{8,}\2'),
    re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----', re.S),
    re.compile(r'(?i)(authorization\s*:\s*bearer\s+)[A-Za-z0-9._~+/=-]{8,}'),
    re.compile(r'AKIA[0-9A-Z]{16}'),
]
SKIP_DIRS_DEFAULT = {'.git','node_modules','vendor','.venv','venv','__pycache__','.pytest_cache','.mypy_cache','coverage'}
PACKAGE_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_SCOPE_TEMPLATE: dict[str, Any] = {
    'version': 'scope-v1',
    'policy': 'local_authorized_target_default',
    'allowed_roots': ['.'],
    'denied_roots': ['.git', 'node_modules', 'vendor', '.venv', 'venv', 'dist/cache', 'evidence/raw'],
    'excluded_extensions': ['.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.7z', '.sqlite', '.db'],
    'max_file_size': 2_000_000,
    'symlink_policy': 'no_follow',
    'network_policy': {
        'default': 'deny',
        'allowed_hosts': ['127.0.0.1', 'localhost'],
        'allowed_private_cidrs': ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'],
        'require_explicit_target_authorization': True,
    },
    'destructive_action_blocklist': ['rm -rf', 'DROP TABLE', 'TRUNCATE TABLE', 'DELETE FROM', 'shutdown', 'format ', 'mkfs', 'curl | sh', 'Invoke-Expression'],
    'secret_redaction_policy': {'enabled': True, 'fail_on_unredacted_secret': True, 'replacement': '<REDACTED>'},
    'evidence_retention_policy': {
        'raw_dir': 'evidence/raw',
        'sanitized_dir': 'evidence/sanitized',
        'report_may_reference_raw': False,
        'keep_raw_local_only': True,
    },
    'confirmed_policy': {
        'severe_requires_dynamic': True,
        'requires_negative_test': True,
        'requires_role_tenant_for_authz': True,
        'ai_generated_content_is_evidence': False,
    },
}

class ScopeError(RuntimeError):
    pass

@dataclass
class ScopeDecision:
    allowed: bool
    reason: str
    path: str | None = None


def load_yaml(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise ScopeError(f'scope_config_missing:{p}')
    text = p.read_text(encoding='utf-8')
    if yaml:
        data = yaml.safe_load(text) or {}
    else:  # minimal fallback for very small configs
        data = {}
        for line in text.splitlines():
            if ':' in line and not line.startswith(' '):
                k,v=line.split(':',1); data[k.strip()] = v.strip() or []
    return data


def find_scope_file(root: str | Path) -> Path | None:
    root = Path(root).resolve()
    local = root / 'scope.yaml'
    if local.exists():
        return local
    package_scope = PACKAGE_ROOT / 'scope.yaml'
    if package_scope.exists() and _is_relative_to(root, PACKAGE_ROOT):
        return package_scope
    return None


def _default_scope_for_root(root: Path) -> dict[str, Any]:
    # A caller-supplied TargetRoot is the local authorization boundary when a
    # target project has not committed its own scope.yaml.  The scope base is
    # deliberately the target root, not the Skills package root, so Windows
    # paths such as C:\work\repo do not get rejected as outside package scope.
    import copy
    data = copy.deepcopy(DEFAULT_SCOPE_TEMPLATE)
    data['_generated_default_scope'] = True
    data['_root'] = str(root)
    data['_scope_file'] = '<generated-target-root-default>'
    data['_scope_base'] = str(root)
    return data


def load_scope(root: str | Path, scope_file: str | Path | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    if scope_file:
        sf = Path(scope_file).resolve()
        if not sf.exists():
            raise ScopeError(f'scope_config_missing:{sf}')
        data = load_yaml(sf)
        scope_base = sf.parent
        scope_file_value = str(sf)
    else:
        sf = find_scope_file(root)
        if sf is None:
            return _default_scope_for_root(root)
        data = load_yaml(sf)
        scope_base = sf.parent
        scope_file_value = str(sf)
    data['_root'] = str(root)
    data['_scope_file'] = scope_file_value
    data['_scope_base'] = str(scope_base)
    # Explicit and fallback scope files define the authorized scan root. Refuse a scan root outside allowed_roots.
    allowed_roots = _resolve_roots(scope_base, data.get('allowed_roots') or ['.'])
    if not any(_is_relative_to(root, ar) for ar in allowed_roots):
        raise ScopeError(f'scan_root_outside_allowed_roots:{root}')
    return data


def _resolve_roots(root: Path, entries: Iterable[str]) -> list[Path]:
    out=[]
    for e in entries or []:
        p = Path(e)
        out.append((root / p).resolve() if not p.is_absolute() else p.resolve())
    return out


def _is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def path_decision(path: str | Path, root: str | Path, scope: dict[str, Any] | None = None) -> ScopeDecision:
    root = Path(root).resolve()
    scope = scope or load_scope(root)
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    try:
        resolved = p.resolve(strict=False)
    except Exception as e:
        return ScopeDecision(False, f'path_resolve_error:{e}', str(p))
    scope_base = Path(scope.get('_scope_base') or root).resolve()
    allowed_roots = _resolve_roots(scope_base, scope.get('allowed_roots') or ['.'])
    denied_roots = _resolve_roots(scope_base, scope.get('denied_roots') or [])
    if not any(_is_relative_to(resolved, ar) for ar in allowed_roots):
        return ScopeDecision(False, 'outside_allowed_roots', str(resolved))
    if any(_is_relative_to(resolved, dr) for dr in denied_roots):
        return ScopeDecision(False, 'inside_denied_roots', str(resolved))
    if p.exists() and p.is_symlink() and scope.get('symlink_policy','no_follow') == 'no_follow':
        return ScopeDecision(False, 'symlink_refused', str(p))
    ext = resolved.suffix.lower()
    if ext and ext in set(scope.get('excluded_extensions') or []):
        return ScopeDecision(False, 'excluded_extension', str(resolved))
    try:
        if resolved.exists() and resolved.is_file() and resolved.stat().st_size > int(scope.get('max_file_size', 2_000_000)):
            return ScopeDecision(False, 'file_too_large', str(resolved))
    except OSError as e:
        return ScopeDecision(False, f'stat_error:{e}', str(resolved))
    return ScopeDecision(True, 'allowed', str(resolved))


def assert_path_allowed(path: str | Path, root: str | Path, scope: dict[str, Any] | None = None) -> Path:
    d = path_decision(path, root, scope)
    if not d.allowed:
        raise ScopeError(f'{d.reason}:{d.path}')
    return Path(d.path or path).resolve()


def iter_scoped_files(root: str | Path, scope: dict[str, Any] | None = None, include_exts: set[str] | None = None) -> Iterator[Path]:
    root = Path(root).resolve()
    scope = scope or load_scope(root)
    include_exts = include_exts or DEFAULT_TEXT_EXTS
    denied_names = set(SKIP_DIRS_DEFAULT)
    for entry in scope.get('denied_roots') or []:
        if not Path(entry).is_absolute():
            denied_names.add(Path(entry).parts[0])
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        d = Path(dirpath)
        dec = path_decision(d, root, scope)
        if not dec.allowed:
            dirnames[:] = []
            continue
        keep=[]
        for dn in dirnames:
            dp = d/dn
            if dn in denied_names or (dp.is_symlink() and scope.get('symlink_policy','no_follow') == 'no_follow'):
                continue
            if path_decision(dp, root, scope).allowed:
                keep.append(dn)
        dirnames[:] = keep
        for fn in filenames:
            p = d/fn
            if p.suffix.lower() not in include_exts and p.suffix:
                continue
            if path_decision(p, root, scope).allowed and p.is_file() and not p.is_symlink():
                yield p


def redact_text(text: str, replacement: str = '<REDACTED>') -> tuple[str, str]:
    redacted = text
    changed = False
    for rx in SECRET_PATTERNS:
        new = rx.sub(lambda m: (m.group(1) + '=' + replacement) if m.lastindex and m.lastindex >= 1 and 'BEGIN' not in m.group(0) else replacement, redacted)
        changed = changed or new != redacted
        redacted = new
    status = 'redacted' if changed else 'clean'
    return redacted, status


def contains_unredacted_secret(text: str) -> bool:
    return any(rx.search(text) for rx in SECRET_PATTERNS)


def read_text_scoped(path: str | Path, root: str | Path, scope: dict[str, Any] | None = None, limit: int | None = None, redact: bool = True) -> tuple[str, str]:
    p = assert_path_allowed(path, root, scope)
    text = p.read_text(encoding='utf-8', errors='ignore')
    if limit is not None:
        text = text[:limit]
    if redact:
        return redact_text(text)
    return text, 'raw'


def sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def payload_decision(payload: str, scope: dict[str, Any]) -> ScopeDecision:
    low = payload.lower()
    for bad in scope.get('destructive_action_blocklist') or []:
        if str(bad).lower() in low:
            return ScopeDecision(False, f'destructive_payload_blocked:{bad}')
    return ScopeDecision(True, 'non_destructive_payload')


def assert_payload_safe(payload: str, scope: dict[str, Any]) -> None:
    d = payload_decision(payload, scope)
    if not d.allowed:
        raise ScopeError(d.reason)


def _host_allowed(host: str, scope: dict[str, Any]) -> bool:
    policy = scope.get('network_policy') or {}
    if host in set(policy.get('allowed_hosts') or []):
        return True
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        for cidr in policy.get('allowed_private_cidrs') or []:
            if ip in ipaddress.ip_network(cidr, strict=False):
                return True
    except Exception:
        return False
    return False


def url_decision(url: str, scope: dict[str, Any]) -> ScopeDecision:
    parsed = urlparse(url)
    if parsed.scheme not in {'http','https','ws','wss'}:
        return ScopeDecision(False, 'unsupported_scheme')
    host = parsed.hostname or ''
    if not _host_allowed(host, scope):
        return ScopeDecision(False, f'host_not_authorized:{host}')
    return ScopeDecision(True, 'authorized_local_or_private_target')


def assert_url_allowed(url: str, scope: dict[str, Any]) -> None:
    d = url_decision(url, scope)
    if not d.allowed:
        raise ScopeError(d.reason)
