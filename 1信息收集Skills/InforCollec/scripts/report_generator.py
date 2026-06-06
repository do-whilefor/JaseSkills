#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, html
from collections import Counter, defaultdict
from _info_collect_lib import common_parser, parse_scope, enforce_scope

def main():
    ap=common_parser('Render information collection report from manifest, graph, quality gate and human review queue.')
    ap.add_argument('--graph', default=None)
    ap.add_argument('--quality', default=None)
    ap.add_argument('--review-queue', default=None)
    ap.add_argument('--html', action='store_true')
    args=ap.parse_args(); path=Path(args.input).resolve(); scope=parse_scope(args.scope,path); ok,reason=enforce_scope(path,scope)
    if not ok: print(json.dumps({'status':'FAIL','reason':reason},ensure_ascii=False)); return 2
    manifest=json.loads(path.read_text(encoding='utf-8',errors='ignore'))
    items=manifest.get('items',[])
    by_type=Counter(it.get('discovered_item_type','unknown') for it in items)
    by_section=defaultdict(list)
    for it in items: by_section[it.get('linked_report_section','evidence-index')].append(it)
    quality=json.loads(Path(args.quality).read_text(encoding='utf-8',errors='ignore')) if args.quality and Path(args.quality).exists() else {}
    review=json.loads(Path(args.review_queue).read_text(encoding='utf-8',errors='ignore')) if args.review_queue and Path(args.review_queue).exists() else {}
    lines=[]
    lines.append('# Information Collection Report')
    lines.append('')
    lines.append('## 授权范围')
    lines.append(f"- Project root: `{manifest.get('project',{}).get('root')}`")
    lines.append('- Network: disabled by default; all evidence is local/static unless explicitly stated.')
    lines.append('')
    lines.append('## 项目指纹 / 技术栈 / 入口点总览')
    lines.append(f"- Evidence items: {len(items)}")
    lines.append(f"- Quality score: {quality.get('score','not-run')} / status: {quality.get('status','not-run')}")
    lines.append(f"- Human review items: {review.get('count', quality.get('human_review_items','not-run'))}")
    lines.append('')
    lines.append('## 信息类型分布')
    for k,v in by_type.most_common(40): lines.append(f'- {k}: {v}')
    sections=[('route-api-inventory','路由/API 清单'),('frontend-js','前端 JS 信息'),('configuration-deployment','配置与部署信息'),('auth-role-tenant','认证/鉴权/角色/租户'),('hidden-information','隐藏信息清单'),('dependency-surface','依赖与供应链线索'),('evidence-index','证据索引')]
    for sec,title in sections:
        rows=by_section.get(sec,[])[:80]
        lines.append(''); lines.append(f'## {title}')
        if not rows: lines.append('- 未发现或未运行对应 collector。'); continue
        lines.append('| Type | Source | Line | Redacted Value | Review |')
        lines.append('|---|---|---:|---|---|')
        for it in rows:
            val=json.dumps(it.get('discovered_item_value_redacted'),ensure_ascii=False)
            val=val.replace('|','\\|')[:240]
            lines.append(f"| {it.get('discovered_item_type')} | `{it.get('source_file')}` | {it.get('source_line_start')} | `{val}` | {it.get('needs_human_review')} |")
    lines.append(''); lines.append('## 未覆盖区域与下一步')
    lines.append('- 运行态 reachability、多角色/多租户 replay、真实外部依赖情报需要在授权本机环境中额外接入。')
    md='\n'.join(lines)+'\n'
    out=Path(args.output) if args.output and args.output!='-' else None
    if args.html:
        body='<html><meta charset="utf-8"><body><pre>'+html.escape(md)+'</pre></body></html>'
        text=body
    else: text=md
    if out: out.write_text(text,encoding='utf-8')
    else: print(text)
    return 0
if __name__=='__main__': raise SystemExit(main())
