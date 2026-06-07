#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check(dashboard: Path, evidence: Path, quality: Path, report_index: Path) -> dict:
    errors=[]
    if not dashboard.exists(): errors.append('dashboard_missing')
    else:
        text=dashboard.read_text(encoding='utf-8', errors='ignore')
        if re.search(r'\b(mock|fake|placeholder|demo only)\b', text, re.I):
            errors.append('dashboard_contains_mock_fake_placeholder_marker')
        if 'traceability only' not in text.lower():
            errors.append('dashboard_missing_non_authoritative_disclaimer')
    for label,p in [('evidence',evidence),('quality',quality),('report_index',report_index)]:
        if not p.exists():
            errors.append(f'{label}_input_missing')
            continue
        try:
            json.loads(p.read_text(encoding='utf-8'))
        except Exception as e:
            errors.append(f'{label}_json_invalid:{e}')
    return {'ok': not errors, 'errors': errors, 'policy':'Dashboard is not accepted as evidence. It passes only when backed by real evidence/quality/report JSON and contains no mock markers.'}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--dashboard', default=str(ROOT/'dashboard/current/index.html'))
    ap.add_argument('--evidence', default=str(ROOT/'outputs/current/engine_evidence_manifest.json'))
    ap.add_argument('--quality', default=str(ROOT/'outputs/current/engine_quality_result.json'))
    ap.add_argument('--report-index', default=str(ROOT/'outputs/current/engine_report.md.json'))
    ap.add_argument('--out', default=str(ROOT/'outputs/current/dashboard_evidence_selftest_result.json'))
    ns=ap.parse_args()
    result=check(Path(ns.dashboard), Path(ns.evidence), Path(ns.quality), Path(ns.report_index))
    Path(ns.out).parent.mkdir(parents=True, exist_ok=True)
    Path(ns.out).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result['ok'] else 1)

if __name__=='__main__': main()
