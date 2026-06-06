#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from _info_collect_lib import enforce_scope, find_unredacted_secrets, parse_scope, stable_hash, scan_inventory  # type: ignore

REQUIRED_EVIDENCE_FIELDS = [
    'evidence_id','collector_name','source_file','source_line_start','source_line_end','discovered_item_type',
    'discovered_item_value_redacted','raw_value_hash','confidence','reason','raw_evidence_hash','redacted_evidence',
    'reproduction_command','limitation','finding_status','collection_time','scope_id'
]
STATUS_VALUES = {'confirmed','candidate','needs_review','rejected','not_reportable','out_of_scope'}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8', errors='ignore'))


def items(data: dict) -> list[dict]:
    return [x for x in data.get('items', []) if isinstance(x, dict)]


def write_report(report: dict, output: str | None) -> int:
    text=json.dumps(report, ensure_ascii=False, indent=2)
    if output and output != '-':
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(text, encoding='utf-8')
    else:
        print(text)
    return 0 if report.get('status') == 'PASS' else 1


def scope_gate(input_path: str, scope_value: str | None, manifest_path: str | None = None) -> dict:
    root=Path(input_path).resolve()
    scope=parse_scope(scope_value, root)
    ok, reason=enforce_scope(root, scope)
    failures=[]
    if not ok:
        failures.append({'path': str(root), 'reason': reason})
    if manifest_path:
        mp=Path(manifest_path).resolve()
        try:
            data=load_json(mp)
            project_root=Path(data.get('project', {}).get('root') or input_path).resolve()
            for idx, it in enumerate(items(data)):
                sf=str(it.get('source_file') or '')
                if not sf or sf == 'unknown':
                    failures.append({'index': idx, 'source_file': sf, 'reason': 'missing source_file'})
                    continue
                p=Path(sf)
                candidate = p if p.is_absolute() else project_root / sf
                ok2, reason2 = enforce_scope(candidate, scope)
                if not ok2 and not str(sf).startswith(str(project_root)):
                    failures.append({'index': idx, 'source_file': sf, 'reason': reason2})
        except Exception as e:
            failures.append({'manifest': manifest_path, 'reason': f'cannot_parse_manifest: {e}'})
    return {'gate': 'scope_gate', 'status': 'PASS' if not failures else 'FAIL', 'failures': failures[:100], 'scope': {'allowed_roots':[str(x) for x in scope.get('allowed_roots', [])], 'denied_paths':[str(x) for x in scope.get('denied_paths', [])]}}


def redaction_gate(manifest_path: str) -> dict:
    data=load_json(Path(manifest_path)); failures=[]
    for idx, it in enumerate(items(data)):
        for field in ['discovered_item_value_redacted','redacted_evidence']:
            paths=find_unredacted_secrets(it.get(field))
            if paths:
                failures.append({'index': idx, 'evidence_id': it.get('evidence_id'), 'field': field, 'paths': paths[:10]})
        if it.get('redaction_status') == 'not_sensitive_or_no_secret_literal' and find_unredacted_secrets(it.get('discovered_item_value_redacted')):
            failures.append({'index': idx, 'evidence_id': it.get('evidence_id'), 'field':'redaction_status', 'reason':'contradicts secret detector'})
    return {'gate':'secret_redaction_gate','status':'PASS' if not failures else 'FAIL','failures':failures[:100], 'checked_items':len(items(data))}


def evidence_completeness_gate(manifest_path: str) -> dict:
    data=load_json(Path(manifest_path)); failures=[]
    for idx, it in enumerate(items(data)):
        missing=[f for f in REQUIRED_EVIDENCE_FIELDS if f not in it or it.get(f) in [None, '']]
        if missing:
            failures.append({'index':idx,'evidence_id':it.get('evidence_id'),'missing':missing})
        if it.get('finding_status') not in STATUS_VALUES:
            failures.append({'index':idx,'evidence_id':it.get('evidence_id'),'field':'finding_status','reason':'invalid status'})
        if isinstance(it.get('source_line_end'), int) and isinstance(it.get('source_line_start'), int) and it['source_line_end'] < it['source_line_start']:
            failures.append({'index':idx,'evidence_id':it.get('evidence_id'),'field':'line_range','reason':'end before start'})
        if it.get('raw_evidence_hash') != it.get('raw_value_hash'):
            # Not always fatal for legacy inputs, but the new manifest builder makes them equal.
            failures.append({'index':idx,'evidence_id':it.get('evidence_id'),'field':'raw_evidence_hash','reason':'does not match raw_value_hash'})
    return {'gate':'evidence_completeness_gate','status':'PASS' if not failures else 'FAIL','failures':failures[:100], 'checked_items':len(items(data)), 'required_fields':REQUIRED_EVIDENCE_FIELDS}


def anti_hallucination_gate(manifest_path: str) -> dict:
    data=load_json(Path(manifest_path)); failures=[]
    for idx, it in enumerate(items(data)):
        status=it.get('finding_status')
        reason=(it.get('reason') or '').lower()
        limitation=(it.get('limitation') or '').lower()
        typ=(it.get('discovered_item_type') or '').lower()
        val=json.dumps(it.get('discovered_item_value_redacted'), ensure_ascii=False, default=str)
        if status == 'confirmed':
            if it.get('needs_human_review'):
                failures.append({'index':idx,'evidence_id':it.get('evidence_id'),'reason':'confirmed item still marked needs_human_review'})
            if not any(x in reason for x in ['confirmed','validated','command output','runtime evidence','schema validated']):
                failures.append({'index':idx,'evidence_id':it.get('evidence_id'),'reason':'confirmed item lacks explicit validation reason'})
        if typ in {'cve','vulnerability_cve'} or 'CVE-' in val:
            verified = it.get('verification_status') == 'verified' and bool(it.get('verification_source'))
            if not verified and not it.get('needs_online_verification') and status != 'rejected':
                failures.append({'index':idx,'evidence_id':it.get('evidence_id'),'reason':'CVE-like claim without needs_online_verification/rejection or explicit verification source'})
        if 'unknown' == str(it.get('source_file')).lower():
            failures.append({'index':idx,'evidence_id':it.get('evidence_id'),'reason':'source_file unknown'})
        if not limitation:
            failures.append({'index':idx,'evidence_id':it.get('evidence_id'),'reason':'missing limitation'})
    return {'gate':'anti_hallucination_gate','status':'PASS' if not failures else 'FAIL','failures':failures[:100], 'rule':'confirmed requires validation reason; CVE requires online verification; no unknown source files'}


def coverage_gate(manifest_path: str, input_path: str | None = None, scope_value: str | None = None) -> dict:
    data=load_json(Path(manifest_path)); its=items(data)
    by_type={}; by_status={}; by_collector={}; sections={}
    for it in its:
        by_type[it.get('discovered_item_type','unknown')]=by_type.get(it.get('discovered_item_type','unknown'),0)+1
        st=it.get('finding_status','candidate'); by_status[st]=by_status.get(st,0)+1
        c=it.get('collector_name','unknown'); by_collector[c]=by_collector.get(c,0)+1
        sec=it.get('linked_report_section','evidence-index'); sections[sec]=sections.get(sec,0)+1
    required_sections={'authorization-scope','project-fingerprint','technology-stack','route-api-inventory','frontend-js','configuration-deployment','dependency-surface','evidence-index'}
    missing=sorted(required_sections-set(sections))
    scan_meta={}
    required_skip_reasons=[]
    if input_path:
        try:
            root=Path(input_path).resolve(); scope=parse_scope(scope_value, root); scan_meta=scan_inventory(root, scope, max_files=5000, timeout=30, scan_profile='standard', follow_symlinks=False)
            marker=root/'.info-end-expected-skips.json'
            if marker.exists() and marker.is_file():
                try:
                    marker_data=json.loads(marker.read_text(encoding='utf-8', errors='ignore'))
                    required_skip_reasons=[str(x) for x in marker_data.get('required_skipped_reasons', [])]
                except Exception as e:
                    required_skip_reasons=[]
                    scan_meta.setdefault('marker_errors', []).append(str(e))
        except Exception as e:
            scan_meta={'error':str(e)}
    missing_required_skip_reasons=[r for r in required_skip_reasons if (scan_meta.get('skipped_reasons') or {}).get(r,0) < 1]
    report={
        'gate':'coverage_gate',
        'status':'PASS' if not missing and len(its)>0 and not missing_required_skip_reasons else 'FAIL',
        'failures': [{'reason':'missing_required_skipped_reason','skipped_reason':r} for r in missing_required_skip_reasons],
        'coverage':{
            'analyzed_files': scan_meta.get('analyzed_files', 'see collector coverage artifacts'),
            'skipped_files': scan_meta.get('skipped_files', 'see collector coverage artifacts'),
            'skipped_reasons': scan_meta.get('skipped_reasons', {}),
            'skipped_file_sample': scan_meta.get('skipped_file_sample', []),
            'endpoint_count':sum(v for k,v in by_type.items() if 'endpoint' in k or 'route' in k or 'api' in k),
            'parameter_count':sum(v for k,v in by_type.items() if 'parameter' in k),
            'js_asset_count':sum(v for k,v in by_type.items() if 'frontend' in k or 'source_map' in k or 'sourcemap' in k or 'service_worker' in k),
            'config_count':sum(v for k,v in by_type.items() if 'config' in k or 'secret' in k or 'iac' in k or 'ci_cd' in k),
            'docs_count':sum(v for k,v in by_type.items() if 'doc' in k),
            'dependency_count':sum(v for k,v in by_type.items() if 'dependency' in k or 'package' in k),
            'evidence_count':len(its),
            'candidate_count':by_status.get('candidate',0),
            'confirmed_count':by_status.get('confirmed',0),
            'needs_review_count':by_status.get('needs_review',0),
            'rejected_count':by_status.get('rejected',0),
            'by_type':by_type,
            'by_collector':by_collector,
            'by_status':by_status,
            'sections':sections,
            'missing_sections':missing,
            'required_skipped_reasons':required_skip_reasons,
            'missing_required_skipped_reasons':missing_required_skip_reasons,
        }
    }
    return report


def unified(input_path: str, scope: str | None, manifest_path: str) -> dict:
    gates=[
        scope_gate(input_path, scope, manifest_path),
        redaction_gate(manifest_path),
        evidence_completeness_gate(manifest_path),
        anti_hallucination_gate(manifest_path),
        coverage_gate(manifest_path, input_path, scope),
    ]
    status='PASS' if all(g.get('status')=='PASS' for g in gates) else 'FAIL'
    return {'schema_version':'info-end-quality-run.v1','status':status,'gates':gates}
