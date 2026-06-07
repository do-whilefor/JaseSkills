#!/usr/bin/env python3
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/fidelity'; OUT.mkdir(parents=True, exist_ok=True)
CATS={'trigger':['trigger','when to use','must trigger','触发','调用'],'forbidden':['forbid','禁止','must not','do not'],'tools':['tool','burp','playwright','mcp','ast','parser'],'templates':['template','模板','vulnerability'],'kb':['knowledge','kb','知识库']}
def snippets(text):
    out=[]
    for i,l in enumerate(text.splitlines(),1):
        low=l.lower(); cats=[c for c,keys in CATS.items() if any(k in low for k in keys)]
        if cats: out.append({'line':i,'text':l[:300],'categories':cats})
    return out
active='\n'.join(p.read_text(encoding='utf-8',errors='ignore')[:2000] for p in list((ROOT/'skills').rglob('*.md'))+list((ROOT/'vulnerability_research_units').rglob('*.md'))+list((ROOT/'config').glob('*.json')))
records=[]; queue=[]; skill_files=list((ROOT/'raw_original_sources').rglob('SKILL.md')) if (ROOT/'raw_original_sources').exists() else []
for sf in skill_files:
    sn=snippets(sf.read_text(encoding='utf-8',errors='ignore')); matched=0
    for s in sn:
        key=' '.join(re.findall(r'[A-Za-z0-9_\-/]{4,}', s['text'].lower())[:5]); matched += 1 if key and key[:40] in active.lower() else 0
    score=matched/len(sn) if sn else 0; rec={'file':str(sf.relative_to(ROOT)),'snippets':len(sn),'matched_approx':matched,'semantic_fidelity_score':round(score,3),'status':'mapped_candidate' if score>=0.55 else 'needs_human_review'}
    records.append(rec); queue += [rec] if rec['status']=='needs_human_review' else []
report={'status':'ok','skill_files':len(skill_files),'records':records,'manual_review_count':len(queue),'policy':'Approximate semantic review; manual review required for low confidence.'}
(OUT/'semantic_fidelity_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); (OUT/'manual_review_queue.json').write_text(json.dumps({'items':queue},ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps({'status':'ok','skill_files':len(skill_files),'manual_review_count':len(queue)},ensure_ascii=False,indent=2))
