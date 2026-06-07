#!/usr/bin/env python3
import json, glob
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'outputs/metrics'; OUT.mkdir(parents=True,exist_ok=True)
def load_jsons(pattern):
    arr=[]
    for f in glob.glob(str(ROOT/pattern), recursive=True):
        try: arr.append(json.loads(Path(f).read_text(encoding='utf-8')))
        except Exception: pass
    return arr
manifests=load_jsons('outputs/**/*manifest*.json'); c=[]
for m in manifests: c.extend(m.get('candidates',[]) if isinstance(m,dict) else [])
counts={s:sum(1 for x in c if x.get('final_status')==s or x.get('state')==s) for s in ['rejected','confirmed','needs_human_review','validation_blocked']}
fields=['source_file','route','method','parameter','auth_context','tenant_context','request_summary','response_summary','code_evidence','dynamic_evidence','negative_control','reproduction_count','impact','quality_gate_score']
comp={}
for vt in sorted(set(x.get('vulnerability_type','unknown') for x in c)):
    subset=[x for x in c if x.get('vulnerability_type','unknown')==vt]
    comp[vt]=sum(sum(1 for f in fields if x.get(f))/len(fields) for x in subset)/len(subset) if subset else 0
metrics={'candidate_count':len(c),'rejected_count':counts['rejected'],'confirmed_count':counts['confirmed'],'needs_human_review_count':counts['needs_human_review'],'validation_blocked_count':counts['validation_blocked'],'false_positive_rate':'unknown_without_manual_ground_truth','false_negative_rate':'unknown_without_benchmark_ground_truth','average_evidence_completeness_by_vulnerability_type':comp,'skill_trigger_accuracy':'unknown_until_regression_labels_loaded','extractor_hit_rate':'unknown_until_benchmark_runner','framework_coverage':sorted([p.name for p in (ROOT/'benchmarks').iterdir() if p.is_dir()]) if (ROOT/'benchmarks').exists() else []}
(OUT/'security_audit_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(metrics,ensure_ascii=False,indent=2))
