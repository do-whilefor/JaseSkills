#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, sys
from _info_collect_lib import common_parser, parse_scope, enforce_scope, now_iso, stable_hash, redact, redaction_status, find_unredacted_secrets

ROOT=Path(__file__).resolve().parents[1]

def load_items(path: Path):
    text=path.read_text(encoding='utf-8', errors='ignore')
    try:
        data=json.loads(text)
        if isinstance(data,dict) and data.get('schema_version') == 'runtime-evidence.v1' and isinstance(data.get('records'), list):
            rows=[]
            for rec in data.get('records') or []:
                if not isinstance(rec, dict):
                    continue
                status = 'confirmed' if rec.get('capture_status') == 'captured' and rec.get('finding_status') == 'confirmed' else 'candidate'
                rows.append({
                    'collector_name':'local_dynamic_validator',
                    'source_file':rec.get('source_file') or 'runtime/local_dynamic_validator.py',
                    'source_line_start':rec.get('source_line_start') or 1,
                    'source_line_end':rec.get('source_line_start') or 1,
                    'source_type':'runtime_evidence',
                    'discovered_item_type':'runtime_endpoint_validation',
                    'discovered_item_value_redacted':rec,
                    'confidence':rec.get('confidence') or (0.95 if status == 'confirmed' else 0.45),
                    'linked_report_section':'dynamic-validation',
                    'needs_human_review':status != 'confirmed',
                    'finding_status':status,
                    'reason':rec.get('reason') or ('confirmed runtime evidence from authorized loopback probe' if status == 'confirmed' else 'runtime evidence did not confirm reachability'),
                    'reproduction_command':f"python runtime/local_dynamic_validator.py --manifest <manifest> --base-url {data.get('base_url','<loopback>')} --output runtime-evidence.json",
                    'limitation':rec.get('limitation') or 'Runtime evidence conversion from local safe probe; no destructive methods and no third-party targets.',
                    'runtime_validation':{'run_id':data.get('run_id'),'mode':data.get('mode'),'schema_version':data.get('schema_version'),'source_evidence_id':rec.get('source_evidence_id')},
                })
            return rows, {'collector_output':str(path),'schema_version':data.get('schema_version'),'collector_name':'local_dynamic_validator'}
        if isinstance(data,dict) and isinstance(data.get('items'),list): return data['items'], {'collector_output':str(path),'schema_version':data.get('schema_version'),'collector_name':data.get('collector_name')}
        if isinstance(data,list): return data, {'collector_output':str(path),'schema_version':'list'}
    except Exception:
        pass
    rows=[]
    for line in text.splitlines():
        try: rows.append(json.loads(line))
        except Exception: pass
    return rows, {'collector_output':str(path),'schema_version':'jsonl'}

def as_int(v, default=1):
    try: return int(v)
    except Exception: return default

def normalize_item(it, idx, provenance, scope_id):
    base=dict(it) if isinstance(it,dict) else {'discovered_item_value_redacted':str(it)}
    typ=str(base.get('discovered_item_type') or base.get('type') or base.get('kind') or 'information_surface')
    sf=str(base.get('source_file') or base.get('path') or 'unknown')
    line=as_int(base.get('source_line_start') or base.get('line') or 1)
    raw_source=base.get('raw_value') if 'raw_value' in base else base.get('value', base.get('discovered_item_value_redacted',''))
    red_value=redact(base.get('discovered_item_value_redacted', raw_source))
    secret_paths=find_unredacted_secrets(red_value)
    eid=base.get('evidence_id') or 'ev-'+stable_hash(f'{sf}:{typ}:{line}:{json.dumps(raw_source,ensure_ascii=False,default=str)}')[:16]
    prov=dict(base.get('collector_provenance') or {})
    prov.update({k:v for k,v in provenance.items() if v is not None})
    prov.setdefault('collector', base.get('collector_name') or provenance.get('collector_name') or 'unknown_collector')
    prov.setdefault('source','local-static')
    prov.setdefault('network','disabled')
    out={
        'evidence_id':eid,
        'kind':'information_surface',
        'collector_name':str(base.get('collector_name') or prov.get('collector') or 'evidence_manifest_builder'),
        'skill_name':str(base.get('skill_name') or 'Info-End'),
        'source_file':sf,
        'source_line_start':line,
        'source_line_end':max(line, as_int(base.get('source_line_end') or line)),
        'source_type':str(base.get('source_type') or 'source'),
        'discovered_item_type':typ,
        'discovered_item_value_redacted':red_value,
        'raw_value_hash':str(base.get('raw_value_hash') or stable_hash(raw_source)),
        'confidence':max(0.0,min(1.0,float(base.get('confidence') if base.get('confidence') is not None else 0.5))),
        'severity_hint':str(base.get('severity_hint') or 'info'),
        'auth_relevance':str(base.get('auth_relevance') or 'unknown'),
        'tenant_relevance':str(base.get('tenant_relevance') or 'unknown'),
        'role_relevance':str(base.get('role_relevance') or 'unknown'),
        'endpoint_relevance':str(base.get('endpoint_relevance') or 'unknown'),
        'data_sensitivity':str(base.get('data_sensitivity') or 'unknown'),
        'reproduction_hint':str(base.get('reproduction_hint') or 'Review linked local evidence only; no network unless authorized.'),
        'collection_time':str(base.get('collection_time') or now_iso()),
        'scope_id':str(base.get('scope_id') or scope_id),
        'false_positive_reason':str(base.get('false_positive_reason') or ''),
        'needs_human_review':bool(base.get('needs_human_review') or secret_paths),
        'linked_report_section':str(base.get('linked_report_section') or 'evidence-index'),
        'path':str(base.get('path') or sf),
        'redaction_status':redaction_status(base.get('discovered_item_value_redacted', raw_source)),
        'collector_provenance':prov,
        'finding_status': str(base.get('finding_status') or base.get('review_status') or ('needs_review' if base.get('needs_human_review') else 'candidate')),
        'reason': str(base.get('reason') or f'{typ} normalized from collector evidence'),
        'raw_evidence_hash': str(base.get('raw_evidence_hash') or base.get('raw_value_hash') or stable_hash(raw_source)),
        'redacted_evidence': red_value,
        'reproduction_command': str(base.get('reproduction_command') or base.get('reproduction_hint') or 'Review local source file and rerun collector inside authorized scope.'),
        'limitation': str(base.get('limitation') or 'Normalized static evidence; not confirmed without explicit runtime/manual verification.'),
    }
    if out['finding_status'] not in {'confirmed','candidate','needs_review','rejected','not_reportable','out_of_scope'}:
        out['finding_status']='candidate'
    if out['finding_status']=='confirmed' and ('confirmed' not in out['reason'].lower() and 'validated' not in out['reason'].lower() and 'runtime evidence' not in out['reason'].lower()):
        out['finding_status']='candidate'
        out['needs_human_review']=True
        out['limitation']=out['limitation'] + ' Confirmed status was downgraded because no explicit validation reason was present.'
    # Preserve controlled verification metadata used by anti-hallucination gates.
    for extra_key in ['verification_status','verification_source','needs_online_verification','runtime_validation','correlation_metrics']:
        if extra_key in base:
            out[extra_key]=base[extra_key]
    # Defend against caller-provided unredacted fields after normalization.
    out['discovered_item_value_redacted']=redact(out['discovered_item_value_redacted'])
    if find_unredacted_secrets(out['discovered_item_value_redacted']):
        out['redaction_status']='redacted'
        out['discovered_item_value_redacted']='****#'+stable_hash(out['discovered_item_value_redacted'])[:12]
        out['needs_human_review']=True
    return out

def validate_manifest(path: Path) -> tuple[bool, str]:
    """Validate the manifest in-process for Windows-safe CLI use."""
    try:
        from jsonschema import Draft202012Validator
        data = json.loads(path.read_text(encoding='utf-8', errors='ignore'))
        schema = json.loads((ROOT / 'schemas' / 'evidence-manifest.schema.json').read_text(encoding='utf-8'))
        errors = []
        for e in sorted(Draft202012Validator(schema).iter_errors(data), key=lambda x: list(x.path))[:100]:
            loc = '.'.join(str(p) for p in e.path) or '<root>'
            errors.append(f'{loc}: {e.message}')
        return not errors, '\n'.join(errors)
    except Exception as e:
        return False, f'validation_error: {e}'

def main():
    ap=common_parser('Build unified evidence manifest from collector JSON/JSONL outputs with forced redaction, dedupe and schema validation.')
    ap.add_argument('--collector-output', action='append', default=[], help='Additional collector JSON/JSONL output')
    ap.add_argument('--allow-invalid', action='store_true', help='Write manifest even if schema validation fails')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope, root); ok,reason=enforce_scope(root, scope)
    if not ok:
        print(json.dumps({'status':'FAIL','reason':reason},ensure_ascii=False)); return 2
    paths=[Path(x) for x in args.collector_output]
    if root.is_file() and not paths: paths=[root]
    items=[]; seen=set(); provenance=[]
    for p in paths:
        if not p.exists():
            continue
        rows, prov=load_items(p); provenance.append(prov)
        for row in rows:
            norm=normalize_item(row, len(items), prov, scope['scope_id'])
            key=(norm['source_file'], norm['source_line_start'], norm['discovered_item_type'], json.dumps(norm['discovered_item_value_redacted'],ensure_ascii=False,sort_keys=True,default=str))
            if key in seen: continue
            seen.add(key); items.append(norm)
    # Add an evidence-index anchor item so downstream reports can always cite the manifest build itself.
    index_item=normalize_item({'collector_name':'evidence_manifest_builder','source_file':str(root),'source_line_start':1,'source_line_end':1,'source_type':'generated_manifest','discovered_item_type':'evidence_manifest_index_built','discovered_item_value_redacted':{'collector_outputs':len(provenance),'unique_items_before_index':len(items)},'confidence':1.0,'linked_report_section':'evidence-index','needs_human_review':False}, len(items), {'collector_output':'evidence_manifest_builder','collector_name':'evidence_manifest_builder'}, scope['scope_id'])
    items.append(index_item)
    manifest={'schema_version':'1.0','project':{'name':root.name,'root':str(root),'base_urls':[]},'generated_at':now_iso(),'items':items,'collector_outputs':provenance,'dedupe':{'input_items':len(items),'unique_items':len(items)}}
    out=Path(args.output) if args.output and args.output!='-' else None
    text=json.dumps(manifest,ensure_ascii=False,indent=2,default=str)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True); out.write_text(text,encoding='utf-8')
        okv,msg=validate_manifest(out)
        if not okv and not args.allow_invalid:
            print(json.dumps({'status':'FAIL','reason':'schema validation failed','validator_output':msg},ensure_ascii=False,indent=2)); return 2
    else:
        print(text)
    return 0
if __name__=='__main__': raise SystemExit(main())
