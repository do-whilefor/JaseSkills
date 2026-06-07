#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import load_scope, assert_path_allowed, assert_url_allowed, ScopeError, load_yaml, sha256_file, redact_text

ROOT = Path(__file__).resolve().parents[1]

def _summary(text: str, limit=3000) -> str:
    redacted, _ = redact_text(text or '')
    return redacted[-limit:]

class ToolOrchestrator:
    def _resolve_executable(self, exe: str) -> str | None:
        if exe in {'python3', 'python'}:
            return sys.executable
        return shutil.which(exe or '')

    def __init__(self, root: str | Path, registry: str | Path | None = None, scope_file: str | Path | None = None):
        self.root = Path(root).resolve()
        self.scope = load_scope(self.root, scope_file)
        self.registry_path = Path(registry or ROOT/'tools/tool_registry.yaml')
        self.registry = load_yaml(self.registry_path)

    def run(self, tool: str, args: list[str] | None = None, target_url: str | None = None, timeout: int = 120) -> dict:
        args = args or []
        spec = (self.registry.get('tools') or {}).get(tool)
        started = time.time()
        base = {
            'schema_version':'tool-result-v1', 'tool':tool, 'status':'unknown', 'available':False,
            'command':[], 'version_command':None, 'version_exit_code':None, 'version_stdout_summary':'', 'version_stderr_summary':'', 'exit_code':None, 'duration_ms':0,
            'stdout_summary':'', 'stderr_summary':'', 'raw_stdout_path':None, 'raw_stderr_path':None,
            'scope_status':'not_checked', 'error':None, 'evidence_refs':[], 'result_is_success':False
        }
        if not spec:
            base.update(status='unavailable', error='tool_not_registered')
            return base
        exe = spec.get('executable')
        exe_path = self._resolve_executable(exe or '')
        if not exe_path:
            base.update(status='unavailable', error='executable_not_found', command=[exe]+(spec.get('default_args') or [])+args)
            return base
        try:
            for a in args:
                if a.startswith('http://') or a.startswith('https://') or a.startswith('ws://') or a.startswith('wss://'):
                    assert_url_allowed(a, self.scope)
                elif a.startswith('/') or a.startswith('.') or Path(a).exists():
                    assert_path_allowed(a, self.root, self.scope)
            if target_url:
                assert_url_allowed(target_url, self.scope)
            if spec.get('requires_network') and not target_url and not any(str(a).startswith(('http://','https://','ws://','wss://')) for a in args):
                raise ScopeError('network_tool_requires_explicit_authorized_target')
            base['scope_status'] = 'allowed'
        except ScopeError as e:
            base.update(status='blocked', available=True, error=str(e), scope_status='blocked')
            return base
        cmd = [exe_path] + [str(x) for x in (spec.get('default_args') or [])] + [str(x) for x in args]
        base['available'] = True; base['command'] = cmd
        # Version is best-effort metadata. Failure is recorded and never converted into tool success.
        version_cmd = [exe_path] + [str(x) for x in (spec.get('version_args') or ['--version'])]
        base['version_command'] = version_cmd
        try:
            vp = subprocess.run(version_cmd, cwd=str(self.root), text=True, capture_output=True, timeout=10)
            base['version_exit_code'] = vp.returncode
            base['version_stdout_summary'] = _summary(vp.stdout or '', 1000)
            base['version_stderr_summary'] = _summary(vp.stderr or '', 1000)
        except Exception as ve:
            base['version_exit_code'] = None
            base['version_stderr_summary'] = repr(ve)
        outdir = self.root/'outputs/current/tool_runs'; outdir.mkdir(parents=True, exist_ok=True)
        stem = f"{tool}-{int(started*1000)}"
        try:
            p = subprocess.run(cmd, cwd=str(self.root), text=True, capture_output=True, timeout=timeout, env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'})
            stdout, stderr = p.stdout or '', p.stderr or ''
            stdout_p, stderr_p = outdir/f'{stem}.stdout.txt', outdir/f'{stem}.stderr.txt'
            stdout_p.write_text(stdout, encoding='utf-8', errors='ignore')
            stderr_p.write_text(stderr, encoding='utf-8', errors='ignore')
            base.update(status='succeeded' if p.returncode == 0 else 'failed', result_is_success=(p.returncode == 0), exit_code=p.returncode,
                        stdout_summary=_summary(stdout), stderr_summary=_summary(stderr),
                        raw_stdout_path=str(stdout_p.relative_to(self.root)), raw_stderr_path=str(stderr_p.relative_to(self.root)),
                        duration_ms=int((time.time()-started)*1000),
                        evidence_refs=[{'path':str(stdout_p.relative_to(self.root)),'sha256':sha256_file(stdout_p)}, {'path':str(stderr_p.relative_to(self.root)),'sha256':sha256_file(stderr_p)}])
            return base
        except subprocess.TimeoutExpired as e:
            base.update(status='failed', error='timeout', duration_ms=int((time.time()-started)*1000), stdout_summary=_summary(e.stdout or ''), stderr_summary=_summary(e.stderr or ''))
            return base
        except Exception as e:
            base.update(status='failed', error=repr(e), duration_ms=int((time.time()-started)*1000))
            return base

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--registry', default=str(ROOT/'tools/tool_registry.yaml'))
    ap.add_argument('--scope-file')
    ap.add_argument('--tool', required=True)
    ap.add_argument('--arg', action='append', default=[])
    ap.add_argument('--target-url')
    ap.add_argument('--out', required=True)
    ns=ap.parse_args()
    orch=ToolOrchestrator(ns.root, ns.registry, ns.scope_file)
    result=orch.run(ns.tool, ns.arg, ns.target_url)
    out=Path(ns.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'tool':ns.tool,'status':result['status'],'available':result['available'],'out':str(out)}, ensure_ascii=False))
    sys.exit(0 if result['status'] == 'succeeded' else 2 if result['status'] == 'blocked' else 3 if result['status'] == 'unavailable' else 1)
if __name__=='__main__': main()
