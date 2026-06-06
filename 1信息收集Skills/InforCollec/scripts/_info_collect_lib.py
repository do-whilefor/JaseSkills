#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, json, math, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

# Build artefacts are intentionally NOT skipped by default. They often contain
# the highest-value JS chunks, source maps, service workers and manifests.
CORE_SKIP_DIRS={'.git','.svn','.hg','node_modules','vendor','.turbo','.cache','.pytest_cache','__pycache__','coverage','.venv','venv','bin','obj'}
SOURCE_ONLY_SKIP_DIRS=CORE_SKIP_DIRS | {'dist','build','.next','.nuxt','target','out','.output'}
TEXT_SUFFIXES={'.py','.js','.jsx','.ts','.tsx','.mjs','.cjs','.java','.php','.rb','.go','.rs','.cs','.kt','.scala','.html','.htm','.css','.scss','.json','.map','.yaml','.yml','.toml','.ini','.env','.conf','.config','.xml','.md','.txt','.graphql','.gql','.proto','.tf','.tfvars','.sh','.ps1','.bat','.properties','.gradle','.pom','.lock','.graphqls'}
SPECIAL_NAMES={'Dockerfile','Makefile','Jenkinsfile','Caddyfile','nginx.conf','apache.conf','httpd.conf','robots.txt','sitemap.xml','security.txt','Taskfile.yml','Taskfile.yaml','Justfile','docker-compose.yml','docker-compose.yaml','compose.yml','compose.yaml','Vagrantfile','Procfile','package-lock.json','pnpm-lock.yaml','yarn.lock','Gemfile','Gemfile.lock','go.sum','Cargo.lock'}
SECRET_KEY_RE=re.compile(r'(?i)(password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key|client[_-]?secret|authorization|cookie|session|jwt|access[_-]?key|refresh[_-]?token|webhook[_-]?secret)')
SECRET_ASSIGNMENT_RE=re.compile(r'''(?ix)(["']?(?:password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key|client[_-]?secret|authorization|cookie|session|jwt|access[_-]?key|refresh[_-]?token|webhook[_-]?secret)["']?)\s*[:=]\s*["']?([^"'\s,#}\]]{6,})''')
TOKEN_LITERAL_RE=re.compile(r'(?i)\b(?:sk_live_[a-z0-9]{8,}|sk_test_[a-z0-9]{8,}|ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{12,}|AKIA[0-9A-Z]{12,}|ASIA[0-9A-Z]{12,}|AIza[0-9A-Za-z_\-]{20,}|eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,})\b')
PRIVATE_KEY_RE=re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----', re.S)
URL_RE=re.compile(r'https?://[^\s"\'<>]+')
PATH_RE=re.compile(r'(?<![A-Za-z0-9_])/(?:api|admin|internal|graphql|v[0-9]|auth|oauth|callback|webhook|debug|health|metrics|socket|ws|rpc|files|upload|download)[A-Za-z0-9_./{}:\-?=&%]*')
ROUTE_RE=re.compile(r'''(?x)
    (?:router|app|server|fastify|blueprint)\s*\.\s*(get|post|put|patch|delete|options|head|use)\s*\(\s*[`"']([^`"']+)
    |@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping|RequestMapping)\s*\(\s*[`"']?([^`"',)]+)
    |(?:Route|path|url)\s*[:=]\s*[`"']([^`"']+)
''')


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def stable_hash(value: Any) -> str:
    if not isinstance(value, str):
        value=json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(value.encode('utf-8','ignore')).hexdigest()

def entropy(s: str) -> float:
    if not s: return 0.0
    freq={c:s.count(c) for c in set(s)}
    return -sum((n/len(s))*math.log2(n/len(s)) for n in freq.values())

def looks_like_secret(value: Any, key_hint: str='') -> bool:
    s=json.dumps(value, ensure_ascii=False, default=str) if not isinstance(value,str) else value
    if not s: return False
    if PRIVATE_KEY_RE.search(s) or TOKEN_LITERAL_RE.search(s) or SECRET_ASSIGNMENT_RE.search(s): return True
    if key_hint and SECRET_KEY_RE.search(key_hint):
        # Redacted placeholders are safe; long unmasked values are not.
        if '****' in s or '<redacted' in s.lower() or '#redacted' in s.lower(): return False
        vals=re.findall(r'[A-Za-z0-9_+./=\-]{10,}', s)
        if vals: return True
    # Generic high entropy tokens with common separators/length. Avoid treating paths as secrets.
    for tok in re.findall(r'(?<![A-Za-z0-9_/.-])[A-Za-z0-9_+./=\-]{28,}(?![A-Za-z0-9_/.-])', s):
        if re.fullmatch(r'[a-fA-F0-9]{32,128}', tok): continue
        if '/' in tok and tok.count('/') >= 2: continue
        if entropy(tok) >= 3.8 and not tok.startswith(('http','/api','/static')): return True
    return False

def redaction_status(value: Any) -> str:
    return 'redacted' if json.dumps(redact(value),ensure_ascii=False,default=str) != json.dumps(value,ensure_ascii=False,default=str) else 'not_sensitive_or_no_secret_literal'

def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out={}
        for k,v in value.items():
            if SECRET_KEY_RE.search(str(k)):
                out[k]=f"****#{stable_hash(v)[:12]}"
            else:
                out[k]=redact(v)
        return out
    if isinstance(value, list):
        return [redact(v) for v in value]
    s=str(value)
    s=PRIVATE_KEY_RE.sub(lambda m: f"{m.group(0).splitlines()[0]}\n****#{stable_hash(m.group(0))[:12]}\n{m.group(0).splitlines()[-1]}", s)
    s=SECRET_ASSIGNMENT_RE.sub(lambda m: f"{m.group(1)}=****#{stable_hash(m.group(2))[:12]}", s)
    s=TOKEN_LITERAL_RE.sub(lambda m: f"****#{stable_hash(m.group(0))[:12]}", s)
    s=re.sub(r'(?i)(bearer\s+)[a-z0-9._\-+/=]{10,}', lambda m: m.group(1)+'****#'+stable_hash(m.group(0))[:12], s)
    return s

def find_unredacted_secrets(obj: Any, prefix: str='') -> list[str]:
    findings=[]
    if isinstance(obj, dict):
        for k,v in obj.items():
            findings += find_unredacted_secrets(v, f'{prefix}.{k}' if prefix else str(k))
            if SECRET_KEY_RE.search(str(k)) and looks_like_secret(v, str(k)):
                findings.append(f'{prefix}.{k}' if prefix else str(k))
    elif isinstance(obj, list):
        for i,v in enumerate(obj):
            findings += find_unredacted_secrets(v, f'{prefix}[{i}]')
    else:
        s=str(obj)
        if '****' not in s and looks_like_secret(s, prefix):
            findings.append(prefix or '<value>')
    return sorted(set(findings))

def read_text(path: Path, limit_bytes: int=2_000_000) -> str:
    try:
        data=path.read_bytes()[:limit_bytes]
        return data.decode('utf-8','ignore')
    except Exception:
        return ''

def parse_scope(scope: str|None, input_path: Path) -> dict:
    allowed=[]; denied=[]; scope_id='default-local-scope'
    if scope:
        p=Path(scope)
        if p.exists() and p.is_file():
            try:
                data=json.loads(p.read_text(encoding='utf-8', errors='ignore'))
                allowed=[Path(x).resolve() for x in data.get('allowed_roots',[]) or data.get('allowed_paths',[])]
                denied=[Path(x).resolve() for x in data.get('denied_paths',[]) or data.get('forbidden_paths',[])]
                scope_id=str(data.get('scope_id') or p.stem)
            except Exception:
                allowed=[p.resolve()]
        else:
            allowed=[p.resolve()]
    if not allowed:
        allowed=[input_path.resolve()]
    return {'scope_id':scope_id,'allowed_roots':allowed,'denied_paths':denied}

def inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False

def enforce_scope(path: Path, scope: dict) -> tuple[bool,str]:
    try: rp=path.resolve()
    except Exception as e: return False, f'path cannot resolve: {e}'
    if any(inside(rp,d) or rp==d for d in scope.get('denied_paths',[])):
        return False, 'path is under denied scope'
    if not any(inside(rp,a) or rp==a for a in scope.get('allowed_roots',[])):
        return False, 'path is outside allowed scope'
    return True, 'ok'

def _skip_dirs_for_profile(scan_profile: str) -> set[str]:
    if scan_profile == 'source-only': return SOURCE_ONLY_SKIP_DIRS
    if scan_profile == 'all': return set()
    # standard and frontend-artifacts scan build artefacts but still skip dependency/cache dirs.
    return CORE_SKIP_DIRS

def is_packaged_symlink_placeholder(path: Path) -> bool:
    """Detect symlink placeholders produced by zip tools on Windows.

    Some archive/extract tools flatten symlinks into small text files containing
    the link target. Treat explicit `*symlink*` marker files as symlinks for
    skip accounting so Windows users keep the same safety behavior without
    needing developer-mode symlink privileges.
    """
    try:
        if path.is_symlink() or not path.is_file():
            return False
        low = path.name.lower()
        if 'symlink' not in low and not low.endswith('.lnk-placeholder'):
            return False
        st = path.stat()
        if st.st_size <= 0 or st.st_size > 4096:
            return False
        target = path.read_text(encoding='utf-8', errors='ignore').strip()
        if not target or '\x00' in target or '\n' in target or '\r' in target:
            return False
        # Link targets in packaged fixtures are usually relative paths. Avoid
        # treating normal text as a placeholder unless it looks like a path.
        return target.startswith(('../', './', '/', '.\\', '..\\')) or bool(re.match(r'^[A-Za-z]:[\\/]', target))
    except Exception:
        return False

def should_scan_file(path: Path, root: Path, scan_profile: str='standard') -> bool:
    name=path.name
    low=name.lower()
    if name in SPECIAL_NAMES or name.startswith('.env'):
        return True
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    if scan_profile in {'frontend-artifacts','standard','all'} and any(part in {'.next','dist','build','.nuxt','out','public','static'} for part in path.parts):
        return path.suffix.lower() in TEXT_SUFFIXES or low.endswith(('.map','.js','.css','.html','.json'))
    return False

def iter_scoped_files(root: Path, scope: dict, max_files: int=5000, timeout: int=30, scan_profile: str='standard', follow_symlinks: bool=False) -> Iterator[Path]:
    start=time.time(); count=0
    root=Path(root)
    roots=[root] if root.is_file() else root.rglob('*')
    skip_dirs=_skip_dirs_for_profile(scan_profile)
    for p in roots:
        if time.time()-start > timeout:
            break
        # Do not follow symlinks by default. Symlink files are skipped before is_file(),
        # because Path.is_file() follows symlinks on many platforms.
        if (p.is_symlink() or is_packaged_symlink_placeholder(p)) and not follow_symlinks:
            continue
        parts=set(p.parts)
        if skip_dirs and parts.intersection(skip_dirs):
            continue
        try:
            if not p.is_file():
                continue
        except Exception:
            continue
        ok,_=enforce_scope(p, scope)
        if not ok:
            continue
        # If following symlinks, verify the resolved target is still in scope.
        if p.is_symlink():
            ok,_=enforce_scope(p.resolve(), scope)
            if not ok:
                continue
        if not should_scan_file(p, root, scan_profile):
            continue
        count += 1
        if max_files and count > max_files:
            break
        yield p



def scan_inventory(root: Path, scope: dict, max_files: int=5000, timeout: int=30, scan_profile: str='standard', follow_symlinks: bool=False, max_skip_records: int=500) -> dict:
    """Return deterministic analyzed/skipped file inventory for coverage gates.

    This is local-only metadata. It does not read file contents. Symlinks are not
    followed unless explicitly requested and then only when the resolved target is
    still inside the authorized scope.
    """
    start=time.time(); analyzed=[]; skipped=[]; counts={}
    def add_skip(path: Path, reason: str):
        counts[reason]=counts.get(reason,0)+1
        if len(skipped) < max_skip_records:
            try: rel=str(path.resolve().relative_to(root.resolve())).replace('\\','/')
            except Exception: rel=str(path)
            skipped.append({'path':rel,'reason':reason})
    root=Path(root)
    iterator=[root] if root.is_file() else root.rglob('*')
    skip_dirs=_skip_dirs_for_profile(scan_profile)
    file_count=0
    for p in iterator:
        if time.time()-start > timeout:
            add_skip(p, 'timeout_reached')
            break
        if (p.is_symlink() or is_packaged_symlink_placeholder(p)) and not follow_symlinks:
            add_skip(p, 'symlink_skipped')
            continue
        if skip_dirs and set(p.parts).intersection(skip_dirs):
            add_skip(p, 'skipped_directory_profile')
            continue
        try:
            if not p.is_file():
                continue
        except Exception:
            add_skip(p, 'stat_failed')
            continue
        ok,reason=enforce_scope(p, scope)
        if not ok:
            add_skip(p, 'out_of_scope:' + reason)
            continue
        if p.is_symlink():
            ok2,reason2=enforce_scope(p.resolve(), scope)
            if not ok2:
                add_skip(p, 'symlink_target_out_of_scope:' + reason2)
                continue
        try:
            # Cheap binary/size diagnostics for coverage reporting.
            st=p.stat()
            if st.st_size > 2_000_000 and scan_profile != 'all':
                add_skip(p, 'large_file_over_2mb')
                continue
            sample=p.read_bytes()[:1024]
            if b'\x00' in sample:
                add_skip(p, 'binary_file')
                continue
        except Exception:
            add_skip(p, 'read_probe_failed')
            continue
        if not should_scan_file(p, root, scan_profile):
            add_skip(p, 'unsupported_suffix_or_name')
            continue
        file_count += 1
        if max_files and file_count > max_files:
            add_skip(p, 'max_files_reached')
            continue
        try: rel=str(p.resolve().relative_to(root.resolve())).replace('\\','/')
        except Exception: rel=str(p)
        analyzed.append(rel)
    return {
        'analyzed_files': len(analyzed),
        'analyzed_file_sample': analyzed[:max_skip_records],
        'skipped_files': sum(counts.values()),
        'skipped_reasons': counts,
        'skipped_file_sample': skipped,
        'scan_profile': scan_profile,
        'follow_symlinks': bool(follow_symlinks),
        'max_files': max_files,
        'timeout_seconds': timeout,
    }

def iter_files(root: Path, max_files: int=5000, timeout: int=30) -> Iterable[Path]:
    # Backward-compatible wrapper; new collectors must use iter_scoped_files().
    scope=parse_scope(None, root)
    return iter_scoped_files(root, scope, max_files=max_files, timeout=timeout, scan_profile='standard', follow_symlinks=False)

def line_no(text: str, needle: str) -> int:
    idx=text.find(needle)
    return 1 if idx < 0 else text[:idx].count('\n')+1

def relpath(source_file: Path, root: Path) -> str:
    try:
        return str(source_file.resolve().relative_to(root.resolve())).replace('\\','/')
    except Exception:
        return str(source_file)

def evidence(collector: str, source_file: Path, root: Path, typ: str, value: Any, line:int=1, source_type:str='source', confidence:float=0.6, severity_hint:str='info', auth_relevance:str='unknown', tenant_relevance:str='unknown', role_relevance:str='unknown', endpoint_relevance:str='unknown', data_sensitivity:str='unknown', reproduction_hint:str='Review local file evidence only; do not contact external targets unless explicitly authorized.', scope_id:str='default-local-scope', needs_review:bool=False, linked_report_section:str='evidence-index', false_positive_reason:str='', collector_provenance:dict|None=None, finding_status:str='candidate', reason:str='', reproduction_command:str='', limitation:str='', **extra: Any) -> dict:
    raw=json.dumps(value, ensure_ascii=False, sort_keys=True, default=str) if not isinstance(value,str) else value
    rel=relpath(source_file, root)
    red=redact(value)
    red_raw=redact(raw)
    out = {
        'evidence_id':'ev-'+stable_hash(f'{collector}:{rel}:{line}:{typ}:{raw}')[:16],
        'kind':'information_surface',
        'collector_name':collector,
        'skill_name':'Info-End',
        'source_file':rel,
        'source_line_start':int(line or 1),
        'source_line_end':int(line or 1),
        'source_type':source_type,
        'discovered_item_type':typ,
        'discovered_item_value_redacted':red,
        'raw_value_hash':stable_hash(raw),
        'confidence':max(0.0,min(1.0,float(confidence))),
        'severity_hint':severity_hint,
        'auth_relevance':auth_relevance,
        'tenant_relevance':tenant_relevance,
        'role_relevance':role_relevance,
        'endpoint_relevance':endpoint_relevance,
        'data_sensitivity':data_sensitivity,
        'reproduction_hint':reproduction_hint,
        'collection_time':now_iso(),
        'scope_id':scope_id,
        'false_positive_reason':false_positive_reason,
        'needs_human_review':bool(needs_review),
        'linked_report_section':linked_report_section,
        'path':rel,
        'redaction_status':'redacted' if red_raw!=raw or json.dumps(red,ensure_ascii=False,default=str)!=json.dumps(value,ensure_ascii=False,default=str) else 'not_sensitive_or_no_secret_literal',
        'collector_provenance': collector_provenance or {'collector':collector,'source':'local-static','network':'disabled'},
        'finding_status': finding_status if finding_status in {'confirmed','candidate','needs_review','rejected','not_reportable','out_of_scope'} else 'candidate',
        'reason': reason or f'{typ} collected by {collector} from authorized local evidence',
        'raw_evidence_hash': stable_hash(raw),
        'redacted_evidence': red,
        'reproduction_command': reproduction_command or f'Review {rel}:{int(line or 1)} and rerun collector {collector} inside the authorized project scope.',
        'limitation': limitation or 'Static collector evidence only; not a confirmed vulnerability or runtime exposure without authorized validation.',
    }
    out.update(extra)
    return out

def output_report(args, collector_name: str, items: list[dict], extra: dict|None=None) -> int:
    report={
        'schema_version':f'{collector_name}.v1',
        'collector_name':collector_name,
        'skill_name':'Info-End',
        'input':str(Path(args.input).resolve()) if getattr(args,'input',None) else None,
        'scope':str(args.scope) if getattr(args,'scope',None) else None,
        'network':'disabled' if getattr(args,'no_network',True) else 'disabled_by_policy',
        'dry_run':bool(getattr(args,'dry_run',False)),
        'generated_at':now_iso(),
        'items':items,
    }
    if extra: report.update(extra)
    text=json.dumps(report, ensure_ascii=False, indent=2 if args.format=='json' else None, default=str)
    out=getattr(args,'output','-') or '-'
    if args.format=='jsonl':
        text='\n'.join(json.dumps(x, ensure_ascii=False, default=str) for x in items) + ('\n' if items else '')
    if out == '-':
        print(text)
    else:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding='utf-8')
    return 0

def common_parser(description: str) -> argparse.ArgumentParser:
    ap=argparse.ArgumentParser(description=description)
    ap.add_argument('--input', required=True, help='Authorized local project/repository root or evidence file')
    ap.add_argument('--output','-o', default='-', help='Output path or -')
    ap.add_argument('--scope', default=None, help='Authorized scope root or scope JSON file')
    ap.add_argument('--format', choices=['json','jsonl'], default='json')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--no-network', action='store_true', default=True)
    ap.add_argument('--redact-secrets', action='store_true', default=True)
    ap.add_argument('--max-files', type=int, default=5000)
    ap.add_argument('--timeout', type=int, default=30)
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--scan-profile', choices=['standard','source-only','frontend-artifacts','all'], default='standard', help='standard scans local source plus build artifacts; source-only excludes build artifacts; frontend-artifacts focuses on generated frontend assets; all only skips explicit scope-blocked files')
    ap.add_argument('--follow-symlinks', action='store_true', help='Follow symlink files only when the resolved target remains inside authorized scope')
    ap.add_argument('--cve-db', default=None, help='Optional local mock/offline vulnerability database JSON for dependency verification; no network is used')
    ap.add_argument('--allow-online-verification', action='store_true', help='Reserved flag: collectors still do not access the network; verified CVE evidence must come from local --cve-db')
    return ap

def dry_run_report(args, collector_name: str, root: Path, scope: dict) -> int:
    ok, reason=enforce_scope(root, scope)
    files=0 if not ok else sum(1 for _ in iter_scoped_files(root, scope, max_files=args.max_files, timeout=max(1,min(args.timeout,5)), scan_profile=getattr(args,'scan_profile','standard'), follow_symlinks=getattr(args,'follow_symlinks',False))) if root.is_dir() else (1 if root.is_file() else 0)
    return output_report(args, collector_name, [], {'scope_check':{'status':'PASS' if ok else 'FAIL','reason':reason,'allowed_roots':[str(x) for x in scope['allowed_roots']],'denied_paths':[str(x) for x in scope['denied_paths']]}, 'files_to_scan':files, 'scan_profile':getattr(args,'scan_profile','standard')})
