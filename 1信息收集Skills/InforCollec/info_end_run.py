#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / 'scripts'
COLLECTORS_DIR = ROOT / 'collectors'
ANALYZERS_DIR = ROOT / 'analyzers'
QUALITY_DIR = ROOT / 'quality'
REPORTS_DIR = ROOT / 'reports'
for _p in [str(SCRIPTS), str(COLLECTORS_DIR), str(ANALYZERS_DIR), str(QUALITY_DIR), str(REPORTS_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

PRE_SCRIPTS = [('scope_guard', 'inline'), ('project_fingerprint', 'inline')]
COLLECTORS = [
    'route_collector', 'js_asset_collector', 'config_collector', 'dependency_collector',
    'docs_collector', 'ci_cd_collector', 'iac_collector', 'graphql_collector',
    'websocket_collector', 'sourcemap_collector', 'hidden_parameter_collector'
]
ANALYZERS = [
    'project_fingerprint_analyzer', 'endpoint_parameter_analyzer', 'auth_surface_analyzer',
    'role_tenant_surface_analyzer', 'frontend_backend_correlation_analyzer',
    'secret_redaction_analyzer', 'evidence_quality_analyzer'
]

SCHEMA_PATHS = {
    'evidence-manifest': ROOT / 'schemas' / 'evidence-manifest.schema.json',
    'collector-output': ROOT / 'schemas' / 'collector-output.schema.json',
    'analyzer-output': ROOT / 'schemas' / 'analyzer-output.schema.json',
    'runtime-evidence': ROOT / 'schemas' / 'runtime-evidence.schema.json',
    'collection-run': ROOT / 'schemas' / 'collection-run.schema.json',
}
_VALIDATOR_CACHE: dict[str, Draft202012Validator] = {}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run(cmd: list[str], timeout: int = 90) -> dict:
    """Run the rare external command with a hard timeout.

    The main Python collection path is intentionally in-process for Windows and
    constrained runners. This helper remains for optional runtime probing only.
    """
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {'cmd': cmd, 'returncode': proc.returncode, 'stdout': proc.stdout[-4000:], 'stderr': proc.stderr[-4000:]}
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout if isinstance(e.stdout, str) else ''
        stderr = e.stderr if isinstance(e.stderr, str) else ''
        return {'cmd': cmd, 'returncode': 124, 'stdout': stdout[-2000:], 'stderr': (stderr + '\ntimeout')[-4000:]}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8', errors='ignore'))


def validate_json_artifact(path: Path, kind: str, name: str, steps: list[dict], schema_results: list[dict]) -> bool:
    errors: list[str] = []
    try:
        obj = _load_json(path)
        if kind not in _VALIDATOR_CACHE:
            _VALIDATOR_CACHE[kind] = Draft202012Validator(_load_json(SCHEMA_PATHS[kind]))
        validator = _VALIDATOR_CACHE[kind]
        for e in sorted(validator.iter_errors(obj), key=lambda x: list(x.path))[:100]:
            loc = '.'.join(str(p) for p in e.path) or '<root>'
            errors.append(f'{loc}: {e.message}')
    except Exception as e:  # pragma: no cover - defensive validation path
        errors.append(f'validation_error: {e}')
    result = {
        'stage': 'schema', 'name': f'{name}:{kind}', 'output': str(path),
        'schema_kind': kind, 'status': 'PASS' if not errors else 'FAIL',
        'returncode': 0 if not errors else 2, 'errors': errors,
    }
    schema_results.append(result)
    steps.append(result)
    return not errors


def write_schema_results(out: Path, schema_results: list[dict]) -> None:
    data = {
        'schema_version': 'info-end-schema-validation.v1',
        'generated_at': now(),
        'status': 'PASS' if all(x.get('status') == 'PASS' for x in schema_results) else 'FAIL',
        'checks': schema_results,
    }
    (out / 'schema-validation.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def make_common_args(args: argparse.Namespace, output: Path) -> SimpleNamespace:
    return SimpleNamespace(
        input=str(Path(args.input).resolve()),
        scope=args.scope or str(Path(args.input).resolve()),
        output=str(output),
        format='json',
        dry_run=bool(args.dry_run),
        no_network=True,
        redact_secrets=True,
        max_files=int(args.max_files),
        timeout=int(args.timeout),
        verbose=bool(args.verbose),
        scan_profile=args.scan_profile,
        follow_symlinks=bool(getattr(args, 'follow_symlinks', False)),
        cve_db=args.cve_db,
        allow_online_verification=False,
    )


def run_scope_guard_inline(args: argparse.Namespace, c_out: Path) -> int:
    from _info_collect_lib import dry_run_report, enforce_scope, evidence, iter_scoped_files, output_report, parse_scope

    a = make_common_args(args, c_out)
    root = Path(a.input).resolve()
    scope = parse_scope(a.scope, root)
    ok, reason = enforce_scope(root, scope)
    if a.dry_run:
        return dry_run_report(a, 'scope_guard', root, scope)
    items: list[dict] = []
    if not ok:
        items.append(evidence('scope_guard', root, root.parent if root.parent.exists() else Path.cwd(), 'out_of_scope_blocked', {'path': str(root), 'reason': reason}, 1, confidence=1.0, severity_hint='blocker', needs_review=True, linked_report_section='authorization-scope'))
        output_report(a, 'scope_guard', items, {'scope_check': {'status': 'FAIL', 'reason': reason, 'allowed_roots': [str(x) for x in scope['allowed_roots']], 'denied_paths': [str(x) for x in scope['denied_paths']]}})
        return 2
    sampled = 0
    if root.is_dir():
        for p in iter_scoped_files(root, scope, a.max_files, a.timeout, a.scan_profile, a.follow_symlinks):
            sampled += 1
            fok, freason = enforce_scope(p, scope)
            if not fok:
                items.append(evidence('scope_guard', p, root, 'out_of_scope_file_blocked', {'path': str(p), 'reason': freason}, 1, confidence=1.0, severity_hint='blocker', needs_review=True, linked_report_section='authorization-scope'))
                break
    items.append(evidence('scope_guard', root, root if root.is_dir() else root.parent, 'authorized_scope_confirmed', {'root': str(root), 'files_sampled': sampled}, 1, confidence=1.0, linked_report_section='authorization-scope'))
    return output_report(a, 'scope_guard', items, {'scope_check': {'status': 'PASS', 'reason': 'input is inside allowed scope', 'allowed_roots': [str(x) for x in scope['allowed_roots']], 'denied_paths': [str(x) for x in scope['denied_paths']]}})


def run_project_fingerprint_inline(args: argparse.Namespace, c_out: Path) -> int:
    import re
    import project_fingerprint as pf
    from _info_collect_lib import dry_run_report, enforce_scope, evidence, iter_scoped_files, output_report, parse_scope, read_text

    a = make_common_args(args, c_out)
    root = Path(a.input).resolve()
    scope = parse_scope(a.scope, root)
    ok, reason = enforce_scope(root, scope)
    if a.dry_run:
        return dry_run_report(a, 'project_fingerprint', root, scope)
    if not ok:
        output_report(a, 'project_fingerprint', [evidence('project_fingerprint', root, root.parent, 'out_of_scope_blocked', reason, 1, confidence=1, severity_hint='blocker', needs_review=True)], {'scope_check': 'FAIL'})
        return 2
    items: list[dict] = []
    counts: dict[str, int] = {}
    frameworks: set[str] = set()
    managers: set[str] = set()
    builds: set[str] = set()
    dirs: set[str] = set()
    topology: set[str] = set()
    workspace_files: list[str] = []
    files = list(iter_scoped_files(root, scope, a.max_files, a.timeout, a.scan_profile, a.follow_symlinks)) if root.is_dir() else [root]
    for p in files:
        rel = str(p.relative_to(root)).replace('\\', '/') if p.is_relative_to(root) else p.name
        if p.suffix in pf.LANG_EXT:
            counts[pf.LANG_EXT[p.suffix]] = counts.get(pf.LANG_EXT[p.suffix], 0) + 1
        if p.name in pf.MANAGERS:
            managers.add(pf.MANAGERS[p.name])
        if p.name in {'pnpm-workspace.yaml', 'turbo.json', 'nx.json', 'rush.json', 'lerna.json'}:
            topology.add('monorepo_workspace')
            workspace_files.append(rel)
        if p.name == 'package.json':
            try:
                pkg = json.loads(read_text(p, 300000))
                if isinstance(pkg, dict) and pkg.get('workspaces'):
                    topology.add('monorepo_workspace')
                    workspace_files.append(rel)
            except Exception:
                pass
        for k, v in pf.BUILD.items():
            if p.name == k or p.name.startswith(k):
                builds.add(v)
        try:
            rel_parts = p.relative_to(root).parts
            if len(rel_parts) > 1:
                dirs.add(rel_parts[0])
        except Exception:
            pass
        text = read_text(p, 300000)
        for fw, pat in pf.FRAMEWORK_PATTERNS:
            if re.search(pat, text, re.I):
                frameworks.add(fw)
    items.append(evidence('project_fingerprint', root, root, 'project_structure', {'top_level_modules': sorted(dirs)[:100], 'file_count_sampled': len(files)}, 1, confidence=.85, linked_report_section='project-fingerprint'))
    if topology:
        items.append(evidence('project_fingerprint', root, root, 'project_topology_detected', {'topologies': sorted(topology), 'workspace_files': sorted(set(workspace_files))}, 1, confidence=.86, linked_report_section='project-fingerprint', reason='Workspace marker files or package.json workspaces indicate monorepo/front-backend package topology', limitation='Static workspace markers do not enumerate every runtime service or deployment boundary'))
    for lang, c in sorted(counts.items()):
        items.append(evidence('project_fingerprint', root, root, 'language_detected', {'language': lang, 'files': c}, 1, confidence=.8, linked_report_section='technology-stack'))
    for fw in sorted(frameworks):
        items.append(evidence('project_fingerprint', root, root, 'framework_detected', fw, 1, confidence=.7, linked_report_section='technology-stack'))
    for m in sorted(managers):
        items.append(evidence('project_fingerprint', root, root, 'package_manager_detected', m, 1, confidence=.8, linked_report_section='technology-stack'))
    for b in sorted(builds):
        items.append(evidence('project_fingerprint', root, root, 'build_or_runtime_tool_detected', b, 1, confidence=.8, linked_report_section='technology-stack'))
    return output_report(a, 'project_fingerprint', items, {'summary': {'languages': counts, 'frameworks': sorted(frameworks), 'package_managers': sorted(managers), 'build_tools': sorted(builds), 'topologies': sorted(topology)}})


def run_collector_inline(args: argparse.Namespace, collector_name: str, c_out: Path) -> int:
    from _collector_core import COLLECTORS as COLLECTOR_FUNCS, collect_dependencies, iter_authorized, out_of_scope_item, output_report, scan_inventory
    from _info_collect_lib import dry_run_report

    a = make_common_args(args, c_out)
    root, scope, ok, reason, files = iter_authorized(a)
    if a.dry_run:
        return dry_run_report(a, collector_name, root, scope)
    if not ok:
        output_report(a, collector_name, [out_of_scope_item(collector_name, root, reason)], {'scope_check': 'FAIL'})
        return 2
    if collector_name == 'dependency_collector':
        items = collect_dependencies(collector_name, root, scope, files, cve_db=getattr(a, 'cve_db', None), allow_online_verification=False)
    elif collector_name == 'js_asset_collector':
        # Avoid nested Node subprocess deadlocks in the one-command Windows/pytest
        # pipeline. Strict AST extraction remains available via
        # scripts/js-ast-endpoint-extractor.mjs and standalone collector runs.
        import os as _os
        previous = _os.environ.get('INFO_END_PIPELINE_NO_NODE_AST')
        _os.environ['INFO_END_PIPELINE_NO_NODE_AST'] = '1'
        try:
            items = COLLECTOR_FUNCS[collector_name](collector_name, root, scope, files)
        finally:
            if previous is None:
                _os.environ.pop('INFO_END_PIPELINE_NO_NODE_AST', None)
            else:
                _os.environ['INFO_END_PIPELINE_NO_NODE_AST'] = previous
    else:
        items = COLLECTOR_FUNCS[collector_name](collector_name, root, scope, files)
    inv = scan_inventory(root, scope, a.max_files, a.timeout, a.scan_profile, a.follow_symlinks) if root.is_dir() else {'analyzed_files': 1, 'skipped_files': 0, 'skipped_reasons': {}, 'skipped_file_sample': []}
    coverage = {
        **inv,
        'collector': collector_name,
        'scope_id': scope['scope_id'],
        'candidate_items': len(items),
        'limitations': ['static local analysis', 'no network verification unless explicit local --cve-db was supplied', 'confirmed status requires manual/runtime evidence'],
    }
    return output_report(a, collector_name, items, {'coverage': coverage})


def build_manifest_inline(inp: str, scope_value: str, out_path: Path, collector_outputs: list[Path], steps: list[dict]) -> bool:
    import evidence_manifest_builder as emb
    from _info_collect_lib import enforce_scope, now_iso, parse_scope, stable_hash

    root = Path(inp).resolve()
    scope = parse_scope(scope_value, root)
    ok, reason = enforce_scope(root, scope)
    if not ok:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps({'status': 'FAIL', 'reason': reason}, ensure_ascii=False, indent=2), encoding='utf-8')
        steps.append({'stage': 'manifest', 'name': 'evidence_manifest_builder', 'output': str(out_path), 'status': 'FAIL', 'returncode': 2, 'stderr': reason})
        return False
    items: list[dict] = []
    seen: set[tuple] = set()
    provenance: list[dict] = []
    for p in collector_outputs:
        if not p.exists():
            continue
        rows, prov = emb.load_items(p)
        provenance.append(prov)
        for row in rows:
            norm = emb.normalize_item(row, len(items), prov, scope['scope_id'])
            key = (norm['source_file'], norm['source_line_start'], norm['discovered_item_type'], json.dumps(norm['discovered_item_value_redacted'], ensure_ascii=False, sort_keys=True, default=str))
            if key in seen:
                continue
            seen.add(key)
            items.append(norm)
    index_item = emb.normalize_item({
        'collector_name': 'evidence_manifest_builder',
        'source_file': str(root),
        'source_line_start': 1,
        'source_line_end': 1,
        'source_type': 'generated_manifest',
        'discovered_item_type': 'evidence_manifest_index_built',
        'discovered_item_value_redacted': {'collector_outputs': len(provenance), 'unique_items_before_index': len(items)},
        'confidence': 1.0,
        'linked_report_section': 'evidence-index',
        'needs_human_review': False,
        'raw_value_hash': stable_hash({'collector_outputs': len(provenance), 'unique_items_before_index': len(items)}),
    }, len(items), {'collector_output': 'evidence_manifest_builder', 'collector_name': 'evidence_manifest_builder'}, scope['scope_id'])
    items.append(index_item)
    manifest = {
        'schema_version': '1.0',
        'project': {'name': root.name, 'root': str(root), 'base_urls': []},
        'generated_at': now_iso(),
        'items': items,
        'collector_outputs': provenance,
        'dedupe': {'input_items': len(items), 'unique_items': len(items)},
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    steps.append({'stage': 'manifest', 'name': 'evidence_manifest_builder', 'output': str(out_path), 'status': 'PASS', 'returncode': 0, 'stderr': 'inline manifest build'})
    return True


def append_step(steps: list[dict], stage: str, name: str, output: Path, returncode: int, stderr: str = '') -> None:
    steps.append({'stage': stage, 'name': name, 'output': str(output), 'status': 'PASS' if returncode == 0 else 'FAIL', 'returncode': returncode, 'stderr': stderr})


def main() -> int:
    ap = argparse.ArgumentParser(description='One-command Info-End engineering pipeline: collectors -> schema validation -> manifest -> analyzers -> quality gates -> reports.')
    ap.add_argument('--input', required=True)
    ap.add_argument('--scope')
    ap.add_argument('--output', required=True)
    ap.add_argument('--max-files', type=int, default=5000)
    ap.add_argument('--timeout', type=int, default=30)
    ap.add_argument('--scan-profile', choices=['standard', 'source-only', 'frontend-artifacts', 'all'], default='standard')
    ap.add_argument('--follow-symlinks', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--no-network', action='store_true', default=True, help='Accepted for policy clarity; pipeline is always offline')
    ap.add_argument('--redact-secrets', action='store_true', default=True, help='Accepted for policy clarity; evidence helper always redacts')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--cve-db', default=None, help='Optional local dependency advisory DB; no network is used')
    ap.add_argument('--base-url', default=None, help='Optional loopback-only base URL for safe runtime validation after static manifest build')
    args = ap.parse_args()

    inp = str(Path(args.input).resolve())
    scope = args.scope or inp
    out = Path(args.output).resolve()
    out.mkdir(parents=True, exist_ok=True)
    steps: list[dict] = []
    schema_results: list[dict] = []
    collector_outputs: list[Path] = []

    for name, _ in PRE_SCRIPTS:
        c_out = out / f'{name}.json'
        if args.verbose:
            print(f'[info_end_run] inline {name}', file=sys.stderr, flush=True)
        try:
            rc = run_scope_guard_inline(args, c_out) if name == 'scope_guard' else run_project_fingerprint_inline(args, c_out)
            append_step(steps, 'pre_collector', name, c_out, rc, 'inline pre-collector')
        except Exception as e:
            rc = 1
            append_step(steps, 'pre_collector', name, c_out, rc, str(e))
        if rc == 0 and c_out.exists() and not args.dry_run:
            collector_outputs.append(c_out)
            validate_json_artifact(c_out, 'collector-output', name, steps, schema_results)

    for c in COLLECTORS:
        c_out = out / f'{c}.json'
        if args.verbose:
            print(f'[info_end_run] inline {c}', file=sys.stderr, flush=True)
        try:
            rc = run_collector_inline(args, c, c_out)
            append_step(steps, 'collector', c, c_out, rc, 'inline collector')
        except Exception as e:
            rc = 1
            append_step(steps, 'collector', c, c_out, rc, str(e))
        if rc == 0 and c_out.exists() and not args.dry_run:
            collector_outputs.append(c_out)
            validate_json_artifact(c_out, 'collector-output', c, steps, schema_results)

    if args.dry_run:
        write_schema_results(out, schema_results)
        summary = {'schema_version': 'collection-run.v1', 'status': 'PASS' if all(s['status'] == 'PASS' for s in steps) else 'FAIL', 'input': inp, 'scope': scope, 'generated_at': now(), 'collectors': steps, 'coverage': {'mode': 'dry-run'}, 'artifacts': {'schema_validation': str(out / 'schema-validation.json')}}
        (out / 'collection-run.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary['status'] == 'PASS' else 1

    manifest = out / 'evidence-manifest.json'
    if args.verbose:
        print('[info_end_run] inline evidence_manifest_builder', file=sys.stderr, flush=True)
    build_manifest_inline(inp, scope, manifest, collector_outputs, steps)
    if manifest.exists():
        validate_json_artifact(manifest, 'evidence-manifest', 'evidence_manifest', steps, schema_results)

    if args.base_url:
        runtime_out = out / 'runtime-evidence.json'
        cmd = [sys.executable, str(ROOT / 'runtime' / 'local_dynamic_validator.py'), '--manifest', str(manifest), '--base-url', args.base_url, '--output', str(runtime_out), '--timeout', str(max(1, min(args.timeout, 10))), '--max-endpoints', '50']
        if args.verbose:
            print(f'[info_end_run] running optional runtime {cmd[1]}', file=sys.stderr, flush=True)
        r = run(cmd, timeout=max(45, args.timeout + 20))
        steps.append({'stage': 'runtime', 'name': 'local_dynamic_validator', 'output': str(runtime_out), 'status': 'PASS' if r['returncode'] == 0 else 'FAIL', 'returncode': r['returncode'], 'stderr': r['stderr']})
        if r['returncode'] == 0 and runtime_out.exists():
            validate_json_artifact(runtime_out, 'runtime-evidence', 'runtime_evidence', steps, schema_results)
            collector_outputs.append(runtime_out)
            build_manifest_inline(inp, scope, manifest, collector_outputs, steps)
            validate_json_artifact(manifest, 'evidence-manifest', 'evidence_manifest_after_runtime', steps, schema_results)

    try:
        from _analyzer_core import ANALYZERS as _ANALYZER_FUNCS, load_manifest as _load_manifest, manifest_items as _manifest_items
        analyzer_data = _load_manifest(manifest)
        analyzer_items = _manifest_items(analyzer_data)
        for a in ANALYZERS:
            a_out = out / f'{a}.json'
            if args.verbose:
                print(f'[info_end_run] inline analyzer {a}', file=sys.stderr, flush=True)
            findings = _ANALYZER_FUNCS[a](analyzer_items)
            result = {'schema_version': 'info-end-analyzer-output.v1', 'generated_at': now(), 'finding_count': len(findings), 'findings': findings}
            a_out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            append_step(steps, 'analyzer', a, a_out, 0, 'inline analyzer')
            validate_json_artifact(a_out, 'analyzer-output', a, steps, schema_results)
    except Exception as e:
        steps.append({'stage': 'analyzer', 'name': 'inline_analyzers', 'output': str(out), 'status': 'FAIL', 'returncode': 1, 'stderr': str(e)})

    q_out = out / 'unified-quality-gate.json'
    try:
        from _quality_core import unified as _unified_quality
        if args.verbose:
            print('[info_end_run] inline quality', file=sys.stderr, flush=True)
        q_data = _unified_quality(inp, scope, str(manifest))
        q_out.write_text(json.dumps(q_data, ensure_ascii=False, indent=2), encoding='utf-8')
        steps.append({'stage': 'quality', 'name': 'unified_quality_gate', 'output': str(q_out), 'status': 'PASS' if q_data.get('status') == 'PASS' else 'FAIL', 'returncode': 0 if q_data.get('status') == 'PASS' else 1, 'stderr': 'inline quality gate'})
    except Exception as e:
        steps.append({'stage': 'quality', 'name': 'unified_quality_gate', 'output': str(q_out), 'status': 'FAIL', 'returncode': 1, 'stderr': str(e)})

    try:
        from _report_core import load as _load_report_data, markdown as _markdown_report, json_report as _json_report, csv_summary as _csv_summary, evidence_manifest_report as _manifest_summary
        report_data = _load_report_data(str(manifest))
        report_specs = [('markdown_report', 'md', _markdown_report), ('json_report', 'json', _json_report), ('csv_summary', 'csv', _csv_summary), ('evidence_manifest_report', 'json', _manifest_summary)]
        for name, ext, func in report_specs:
            dest = out / f'{name}.{ext}'
            if args.verbose:
                print(f'[info_end_run] inline report {dest.name}', file=sys.stderr, flush=True)
            dest.write_text(func(report_data), encoding='utf-8')
            append_step(steps, 'report', name, dest, 0, 'inline report generation')
    except Exception as e:
        steps.append({'stage': 'report', 'name': 'inline_reports', 'output': str(out), 'status': 'FAIL', 'returncode': 1, 'stderr': str(e)})

    write_schema_results(out, schema_results)
    quality = {}
    if q_out.exists():
        try:
            quality = _load_json(q_out)
        except Exception:
            quality = {}
    coverage = {}
    if manifest.exists():
        try:
            m = _load_json(manifest)
            its = m.get('items', [])
            coverage = {
                'evidence_count': len(its),
                'candidate_count': sum(1 for x in its if x.get('finding_status') == 'candidate'),
                'needs_review_count': sum(1 for x in its if x.get('finding_status') == 'needs_review'),
                'confirmed_count': sum(1 for x in its if x.get('finding_status') == 'confirmed'),
            }
        except Exception:
            pass
    status = 'PASS' if all(s['status'] == 'PASS' for s in steps) else 'FAIL'
    summary = {
        'schema_version': 'collection-run.v1',
        'status': status,
        'input': inp,
        'scope': scope,
        'generated_at': now(),
        'collectors': [s for s in steps if s['stage'] in {'pre_collector', 'collector'}],
        'steps': steps,
        'coverage': coverage,
        'quality': quality,
        'artifacts': {
            'manifest': str(manifest),
            'quality': str(q_out),
            'schema_validation': str(out / 'schema-validation.json'),
            'runtime_evidence': str(out / 'runtime-evidence.json') if args.base_url else None,
            'markdown_report': str(out / 'markdown_report.md'),
            'json_report': str(out / 'json_report.json'),
            'csv_summary': str(out / 'csv_summary.csv'),
        },
    }
    (out / 'collection-run.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    validate_json_artifact(out / 'collection-run.json', 'collection-run', 'collection_run', steps, schema_results)
    write_schema_results(out, schema_results)
    status = 'PASS' if all(s['status'] == 'PASS' for s in steps) else 'FAIL'
    summary['status'] = status
    summary['steps'] = steps
    summary['artifacts']['schema_validation'] = str(out / 'schema-validation.json')
    (out / 'collection-run.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if status == 'PASS' else 1


if __name__ == '__main__':
    import os
    _rc = main()
    try:
        sys.stdout.flush(); sys.stderr.flush()
    finally:
        os._exit(int(_rc))
