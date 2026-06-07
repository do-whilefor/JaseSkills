#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.scope_guard import load_yaml


def check(rules_file: str | Path) -> dict:
    data = load_yaml(rules_file)
    errors = []
    ids = set()
    for idx, rule in enumerate(data.get('rules') or []):
        rid = rule.get('id')
        if not rid:
            errors.append({'index': idx, 'code':'detector_id_missing'})
            continue
        if rid in ids:
            errors.append({'id': rid, 'code':'detector_id_duplicate'})
        ids.add(rid)
        if not rule.get('title'):
            errors.append({'id': rid, 'code':'title_missing'})
        if not any(rule.get(k) for k in ['file_patterns','sink_patterns','source_patterns']):
            errors.append({'id': rid, 'code':'empty_detector_no_static_or_sink_logic'})
        if rule.get('severity_candidate') in {'high','critical'} and 'requires_role_tenant' not in rule:
            errors.append({'id': rid, 'code':'severe_detector_missing_role_tenant_policy'})
    return {'ok': not errors, 'detectors': len(ids), 'errors': errors}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rules', default=str(Path(__file__).resolve().parents[1] / 'detectors/detector_rules.yaml'))
    ap.add_argument('--out')
    ns = ap.parse_args()
    result = check(ns.rules)
    if ns.out:
        Path(ns.out).parent.mkdir(parents=True, exist_ok=True)
        Path(ns.out).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result['ok'] else 1)

if __name__ == '__main__':
    main()
