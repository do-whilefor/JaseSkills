#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def rel(p: Path, root: Path):
    try: return str(p.relative_to(root))
    except Exception: return str(p)

def exists_all(root, items): return [x for x in items if (root/x).exists()]

def classify_skill(path: Path, root: Path, bindings: dict):
    files=[p for p in path.rglob('*') if p.is_file()]
    name=path.name
    bind=bindings.get(name, {})
    impl=bind.get('implementations',[]); schemas=bind.get('schemas',[]); tests=bind.get('tests',[])
    impl_ok=exists_all(root,[Path(x) for x in impl]); schema_ok=exists_all(root,[Path(x) for x in schemas]); test_ok=exists_all(root,[Path(x) for x in tests])
    has_skill=(path/'SKILL.md').exists()
    text='\n'.join(p.read_text(encoding='utf-8',errors='ignore')[:2000] for p in files if p.suffix in {'.md','.json','.yaml','.yml'} and p.stat().st_size<200000)
    defects=[]
    if not has_skill: defects.append('missing_SKILL_md')
    if impl and len(impl_ok)!=len(impl): defects.append('bound_implementation_missing:'+','.join(sorted(set(impl)-{str(x) for x in impl_ok})))
    if not impl: defects.append('no_bound_implementation')
    if schemas and len(schema_ok)!=len(schemas): defects.append('bound_schema_missing')
    if not schemas: defects.append('no_bound_schema')
    if tests and len(test_ok)!=len(tests): defects.append('bound_test_missing')
    if not tests: defects.append('no_bound_test')
    if re.search(r'(?i)百分百|0day|confirmed without|已确认', text): defects.append('strong_claim_review_required')
    status=bind.get('status') or ('needs_review' if defects else 'promoted')
    if defects and status=='promoted': status='needs_review'
    return {'skill_path':rel(path,root),'current_capability':'bound to '+', '.join(impl) if impl else 'documentation entrypoint','real_executability':'executable_binding_present' if impl_ok else 'documentation_only','bound_implementations':impl,'bound_schemas':schemas,'bound_tests':tests,'defects':defects,'promotion':status,'safety_impact':'may cause hallucinated readiness' if defects else 'controlled by quality gate'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='.'); ap.add_argument('--out',required=True); ns=ap.parse_args(); root=Path(ns.root).resolve()
    bfile=root/'config/skill_capability_bindings.json'
    bindings=json.loads(bfile.read_text(encoding='utf-8')).get('bindings',{}) if bfile.exists() else {}
    skills=[]
    for p in sorted((root/'skills').iterdir()) if (root/'skills').exists() else []:
        if p.is_dir(): skills.append(classify_skill(p,root,bindings))
    summary={'total_skills':len(skills),'promoted':sum(1 for s in skills if s['promotion']=='promoted'),'promoted_candidate_only':sum(1 for s in skills if s['promotion']=='promoted_candidate_only'),'promoted_engine_only':sum(1 for s in skills if s['promotion']=='promoted_engine_only'),'needs_review':sum(1 for s in skills if s['promotion']=='needs_review'),'blocked':sum(1 for s in skills if s['promotion']=='blocked'),'policy':'promotion is based on executable bindings, schema, test, evidence and quality gate; static candidate capabilities are candidate-only'}
    out={'schema_version':'capability-audit-v1','summary':summary,'skills':skills}
    Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,**summary},ensure_ascii=False))
if __name__=='__main__': main()
