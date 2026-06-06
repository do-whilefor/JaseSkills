#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, html
from collections import defaultdict
from _info_collect_lib import common_parser, parse_scope, enforce_scope

def main():
    ap=common_parser('Generate static HTML dashboard drill-down: Route -> Evidence -> Graph -> Review -> Report Section.')
    ap.add_argument('--graph', default=None)
    ap.add_argument('--review-queue', default=None)
    args=ap.parse_args(); path=Path(args.input).resolve(); scope=parse_scope(args.scope,path); ok,reason=enforce_scope(path,scope)
    if not ok: print(json.dumps({'status':'FAIL','reason':reason},ensure_ascii=False)); return 2
    data=json.loads(path.read_text(encoding='utf-8',errors='ignore')); items=data.get('items',[])
    section=defaultdict(list)
    for it in items: section[it.get('linked_report_section','evidence-index')].append(it)
    rows=[]
    for sec,its in sorted(section.items()):
        rows.append(f'<h2>{html.escape(sec)}</h2><table border="1"><tr><th>Type</th><th>Source</th><th>Line</th><th>Value</th><th>Review</th></tr>')
        for it in its[:200]:
            val=html.escape(json.dumps(it.get('discovered_item_value_redacted'),ensure_ascii=False)[:300])
            rows.append(f"<tr><td>{html.escape(str(it.get('discovered_item_type')))}</td><td>{html.escape(str(it.get('source_file')))}</td><td>{it.get('source_line_start')}</td><td><code>{val}</code></td><td>{it.get('needs_human_review')}</td></tr>")
        rows.append('</table>')
    body='<html><meta charset="utf-8"><title>Info-End Dashboard</title><body><h1>Info-End Dashboard Drilldown</h1><p>Candidate evidence only; manual review required before vulnerability claims.</p>'+''.join(rows)+'</body></html>'
    if args.output=='-': print(body)
    else: Path(args.output).write_text(body,encoding='utf-8')
    return 0
if __name__=='__main__': raise SystemExit(main())
