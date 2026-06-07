#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re, sys, subprocess
from pathlib import Path
try:
    import yaml
except Exception:
    yaml = None
ROOT = Path(__file__).resolve().parents[1]
STATUSES = ['positive','negative','blocked','needs_review']


def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception:
        return default


def load_rules():
    if not yaml:
        return []
    return yaml.safe_load((ROOT/'detectors/detector_rules.yaml').read_text(encoding='utf-8')).get('rules', [])


def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    return {'cmd':' '.join(map(str, cmd)), 'returncode': p.returncode, 'stdout': p.stdout[-2000:], 'stderr': p.stderr[-2000:]}


def file_contains(path, pattern):
    try:
        return re.search(pattern, Path(path).read_text(encoding='utf-8'), re.S) is not None
    except Exception:
        return False


def audit():
    rules = load_rules()
    failures = {'blocking': [], 'high': [], 'medium': [], 'low': []}
    false_capabilities = []
    leak_risks = []
    fp_risks = []
    evidence_breaks = []
    dynamic_breaks = []
    quality_breaks = []

    # Parser capability proof.
    parser_notes = load_json(ROOT/'outputs/current/semantic_ast_status.json', {}) or {}
    for lang, paths in {
        'java': ['analyzers/lang/java_ast.py','analyzers/lang/probes/JavaAstProbe.java'],
        'go': ['analyzers/lang/go_ast.py','analyzers/lang/probes/GoAstProbe.go'],
        'ruby': ['analyzers/lang/ruby_ast.py','analyzers/lang/probes/RubyRipperProbe.rb'],
    }.items():
        if not all((ROOT/p).exists() for p in paths):
            failures['high'].append({'id': f'PARSER-{lang}', 'issue': 'parser implementation file missing', 'path': paths})
    php = (ROOT/'analyzers/lang/php_ast.py').read_text(encoding='utf-8')
    rust = (ROOT/'analyzers/lang/rust_ast.py').read_text(encoding='utf-8')
    if 'PhpStructuralProbe' in php and 'tree_sitter_available' in php:
        false_capabilities.append({'capability':'PHP full AST', 'verdict':'initial-only', 'reason':'tree-sitter preferred, PHP tokenizer structural fallback is not complete AST'})
    if 'parser_unavailable' in rust:
        false_capabilities.append({'capability':'Rust full AST', 'verdict':'paper-or-environment-dependent', 'reason':'requires tree-sitter Rust or rustc nightly; unavailable environments must not claim AST coverage'})

    # Detector source-sink proof.
    dr = (ROOT/'detectors/detector_runner.py').read_text(encoding='utf-8')
    if '_path_to_sink' not in dr or 'cross_file_dataflow' not in dr:
        failures['blocking'].append({'id':'DETECTOR-DATAFLOW-ABSENT','issue':'detector has no source-sink traversal'})
    if 'source_scan' in dr:
        false_capabilities.append({'capability':'all detector findings have source-sink-dataflow', 'verdict':'false', 'reason':'detector has source_scan weak-signal pass; quality gate must block confirmed without cross_file_dataflow'})
    for r in rules:
        rid = r.get('id')
        base = ROOT/'tests/fixtures/vulnerable_apps'/rid
        missing = [s for s in STATUSES if not (base/s).exists()]
        if missing:
            failures['high'].append({'id':'FIXTURE-MISSING','detector':rid,'missing':missing})

    # Evidence/report gate proof.
    if 'quality_gate_not_passed_report_blocked' not in (ROOT/'report/report_generator.py').read_text(encoding='utf-8'):
        failures['blocking'].append({'id':'REPORT-QUALITY-BYPASS','issue':'report can be generated when quality gate failed'})
        quality_breaks.append('report_generator_does_not_block_quality_fail')
    if 'sanitized_path_outside_manifest_root' not in (ROOT/'evidence/ref_validator.py').read_text(encoding='utf-8'):
        failures['blocking'].append({'id':'EVIDENCE-OUTSIDE-ROOT','issue':'evidence validator does not reject outside-root sanitized evidence'})
        evidence_breaks.append('sanitized_path_outside_root_not_blocked')
    if 'severe_confirmed_requires_cross_file_source_sink_dataflow' not in (ROOT/'quality/quality_gate.py').read_text(encoding='utf-8'):
        failures['blocking'].append({'id':'QUALITY-DATAFLOW-PROMOTION','issue':'severe finding can be confirmed without source-sink dataflow'})
        quality_breaks.append('severe_without_dataflow_can_promote')
    if 'replay_schema_invalid' not in (ROOT/'quality/quality_gate.py').read_text(encoding='utf-8'):
        failures['high'].append({'id':'REPLAY-SCHEMA-NOT-GATED','issue':'replay output schema is not checked by quality gate'})

    # Dynamic proof.
    pr = (ROOT/'dynamic/playwright_runner.py').read_text(encoding='utf-8')
    for term in ['record_har_path','tracing.start','page.screenshot','page.content','console','request','response','storage_state']:
        if term not in pr:
            failures['high'].append({'id':'PLAYWRIGHT-MISSING-'+term, 'issue':'dynamic evidence capture term missing'})
    dynamic_breaks.extend([
        'no bundled real target_url or credentials; runner must output needs_manual_target/unavailable, not confirmed',
        'role_tenant_matrix.yaml is example/default until project-specific accounts are configured',
        'negative_control is represented in plan and quality gate, but semantic assertion of deny/allow still needs target-specific oracle',
    ])

    # 0day/harness proof.
    if not (ROOT/'fuzz/fuzz_harness.py').exists() or not (ROOT/'tests/property/invariants.py').exists():
        failures['medium'].append({'id':'0DAY-HARNESS-MISSING','issue':'fuzz harness or invariant file missing'})
    else:
        false_capabilities.append({'capability':'0day research automation', 'verdict':'initial-only', 'reason':'harness/invariants exist, but target-specific generators/oracles are not complete'})

    # Dashboard proof.
    for dash in [ROOT/'dashboard/index.html', ROOT/'dashboard/current/index.html']:
        if dash.exists() and ('mock' in dash.read_text(encoding='utf-8', errors='ignore').lower()):
            false_capabilities.append({'capability':'dashboard is fully real-time', 'verdict':'suspect', 'reason':f'{dash.relative_to(ROOT)} contains mock wording/data'})
    false_capabilities.append({'capability':'dashboard is authoritative evidence source', 'verdict':'false', 'reason':'dashboard is display-only; quality/evidence/report JSON are authoritative'})

    leak_risks.extend([
        {'risk':'parser coverage gaps', 'why':'PHP structural fallback and Rust parser_unavailable can miss framework-specific sinks/routes', 'needed':'tree-sitter/php-parser/rust parser fixtures and graph adapter'},
        {'risk':'semantic dataflow gaps', 'why':'call resolution is name-based and not type/interprocedural/context-sensitive', 'needed':'language-specific symbol tables, import resolution, taint propagation'},
        {'risk':'business logic/state machine bugs', 'why':'detectors are static signals plus limited graph paths', 'needed':'target-specific invariant tests and replay oracles'},
        {'risk':'authz/multi-tenant gaps', 'why':'requires configured role/tenant matrix and logged-in states', 'needed':'project matrix with accounts and expected allow/deny assertions'},
    ])
    fp_risks.extend([
        {'risk':'file-signal candidate may not be reachable', 'block':'quality gate prevents confirmed unless cross_file_dataflow and dynamic evidence exist'},
        {'risk':'sink call may use constant safe input', 'block':'negative test + source-controlled proof required'},
        {'risk':'tool alert copied as finding', 'block':'tool output cannot substitute evidence manifest/replay'},
    ])
    evidence_breaks.extend([
        'evidence_manifest_builder creates static source evidence only; dynamic artifacts must be attached after Playwright/HAR import',
        'dynamic runner result is separate from evidence manifest until imported/stitched by evidence collector',
        'tool orchestrator outputs are tool results, not vulnerability evidence unless converted into manifest entries and sanitized',
    ])
    quality_breaks.extend([
        'quality gate can only evaluate provided JSON; if pipeline bypasses it, report_generator must block missing/failed quality',
        'candidate findings may appear in reports with limitations; they must not be interpreted as confirmed',
    ])

    return {
        'schema_version':'ultimate-accountability-audit-v1',
        'summary': {'blocking': len(failures['blocking']), 'high': len(failures['high']), 'medium': len(failures['medium']), 'low': len(failures['low'])},
        'failures': failures,
        'false_capabilities': false_capabilities,
        'leak_risks': leak_risks,
        'false_positive_risks': fp_risks,
        'evidence_breaks': evidence_breaks,
        'dynamic_breaks': dynamic_breaks,
        'quality_breaks': quality_breaks,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ns = ap.parse_args()
    data = audit()
    Path(ns.out).parent.mkdir(parents=True, exist_ok=True)
    Path(ns.out).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(data['summary'], ensure_ascii=False))
    # The audit is allowed to succeed while documenting known limitations.
    sys.exit(0)


if __name__ == '__main__':
    main()
