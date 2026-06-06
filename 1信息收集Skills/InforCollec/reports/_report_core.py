#!/usr/bin/env python3
from __future__ import annotations
import argparse
import csv
import json
from io import StringIO
from pathlib import Path
from datetime import datetime, timezone


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8', errors='ignore'))


def items(data: dict) -> list[dict]:
    return [x for x in data.get('items', []) if isinstance(x, dict)]


def counts(its: list[dict]) -> dict:
    out={'total':len(its),'by_status':{},'by_type':{},'by_collector':{},'by_section':{}}
    for it in its:
        for key, field in [('by_status','finding_status'),('by_type','discovered_item_type'),('by_collector','collector_name'),('by_section','linked_report_section')]:
            val=str(it.get(field,'unknown'))
            out[key][val]=out[key].get(val,0)+1
    return out


def markdown(data: dict) -> str:
    its=items(data); c=counts(its)
    lines=['# Info-End Information Collection Report','',f"Generated: {datetime.now(timezone.utc).replace(microsecond=0).isoformat()}",f"Project: {data.get('project',{}).get('name','unknown')}",f"Root: {data.get('project',{}).get('root','unknown')}",'','## Coverage Summary','']
    for k,v in c.items():
        lines.append(f'- {k}: `{json.dumps(v, ensure_ascii=False)}`')
    lines += ['','## Evidence Items','','| Status | Type | Collector | Source | Line | Reason | Limitation |','|---|---|---|---|---:|---|---|']
    for it in its[:500]:
        lines.append('| {status} | {typ} | {collector} | `{src}` | {line} | {reason} | {limitation} |'.format(
            status=it.get('finding_status','candidate'), typ=it.get('discovered_item_type',''), collector=it.get('collector_name',''), src=it.get('source_file',''), line=it.get('source_line_start',''), reason=str(it.get('reason','')).replace('|','/'), limitation=str(it.get('limitation','')).replace('|','/')
        ))
    lines += ['','All records remain candidate or needs_review unless explicit confirmed validation evidence is present.']
    return '\n'.join(lines)+'\n'


def json_report(data: dict) -> str:
    its=items(data)
    return json.dumps({'schema_version':'info-end-json-report.v1','project':data.get('project'), 'coverage':counts(its), 'items':its}, ensure_ascii=False, indent=2)


def csv_summary(data: dict) -> str:
    its=items(data); buf=StringIO(); w=csv.writer(buf)
    w.writerow(['evidence_id','status','type','collector','source_file','line','confidence','needs_human_review','reason','limitation'])
    for it in its:
        w.writerow([it.get('evidence_id'),it.get('finding_status'),it.get('discovered_item_type'),it.get('collector_name'),it.get('source_file'),it.get('source_line_start'),it.get('confidence'),it.get('needs_human_review'),it.get('reason'),it.get('limitation')])
    return buf.getvalue()


def evidence_manifest_report(data: dict) -> str:
    return json.dumps({'schema_version':'evidence-manifest-report.v1','project':data.get('project'), 'generated_at':data.get('generated_at'), 'collector_outputs':data.get('collector_outputs',[]), 'evidence_count':len(items(data)), 'coverage':counts(items(data))}, ensure_ascii=False, indent=2)

FORMATS={'markdown':markdown,'json':json_report,'csv':csv_summary,'manifest-summary':evidence_manifest_report}


def run(fmt: str) -> int:
    ap=argparse.ArgumentParser(description=f'Generate {fmt} report from evidence manifest')
    ap.add_argument('--input', required=True); ap.add_argument('--output','-o', default='-')
    a=ap.parse_args(); text=FORMATS[fmt](load(a.input))
    if a.output and a.output!='-':
        Path(a.output).parent.mkdir(parents=True, exist_ok=True); Path(a.output).write_text(text, encoding='utf-8')
    else:
        print(text, end='')
    return 0
