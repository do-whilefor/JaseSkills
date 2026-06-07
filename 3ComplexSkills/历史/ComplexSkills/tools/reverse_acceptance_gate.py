#!/usr/bin/env python3
"""Second reverse-audit acceptance gate.
It checks detector fixtures, detector outputs, strict manifests, report evidence ids,
secret redaction, dashboard provenance and package hygiene. It is intentionally stricter
than normal smoke tests and fails closed on hallucination-prone gaps.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, re, importlib.util
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
try:
    import jsonschema
except Exception:
    jsonschema=None

def load(p: Path) -> Any: return json.loads(p.read_text(encoding='utf-8',errors='ignore'))
def rel(p: Path) -> str:
    try: return str(p.resolve().relative_to(ROOT))
    except Exception: return str(p)
def validate(schema_path: Path, obj: Any) -> list[str]:
    if jsonschema is None: return ['jsonschema package unavailable']
    schema=load(schema_path)
    return [f"{'.'.join(map(str,e.absolute_path)) or '<root>'}: {e.message}" for e in jsonschema.Draft202012Validator(schema).iter_errors(obj)]

def check_detectors() -> tuple[list[str],dict[str,Any]]:
    errors=[]; details={'detectors':0,'fixtures':0}
    schema=ROOT/'schemas/extended_detector.schema.json'
    dets=sorted((ROOT/'skills/07-vulnerability-hunting-engine/detectors/extended_40').glob('D*.json'))
    details['detectors']=len(dets)
    if len(dets)!=40: errors.append(f'expected 40 extended detectors, got {len(dets)}')
    for f in dets:
        d=load(f); errors += [f'{rel(f)} schema: {e}' for e in validate(schema,d)]
        did=d.get('detector_id')
        for kind,path in (d.get('fixtures') or {}).items():
            fp=ROOT/path
            if not fp.exists(): errors.append(f'{rel(f)} missing {kind} fixture {path}'); continue
            details['fixtures']+=1
            fx=load(fp)
            if fx.get('detector_id')!=did: errors.append(f'{path} detector_id mismatch')
            if fx.get('fixture_kind')!=kind: errors.append(f'{path} fixture_kind mismatch')
            if fx.get('should_emit_confirmed') is not False: errors.append(f'{path} must not emit confirmed')
    return errors, details

def check_detector_output(path: str|None) -> tuple[list[str],dict[str,Any]]:
    if not path: return [], {'skipped':True}
    p=Path(path); obj=load(p); errors=validate(ROOT/'schemas/detector_output.schema.json',obj)
    for i,c in enumerate(obj.get('candidates') or []):
        if c.get('state')=='confirmed': errors.append(f'candidates[{i}] illegally confirmed')
        if not c.get('evidence_id'): errors.append(f'candidates[{i}] missing evidence_id')
        if c.get('dynamic_status')=='executed_confirmed': errors.append(f'candidates[{i}] detector output cannot carry executed_confirmed')
    return errors, {'candidate_count':obj.get('candidate_count',0),'schema_version':obj.get('schema_version')}

def manifest_paths(base: Path) -> list[Path]:
    if not base.exists(): return []
    return [p for p in base.rglob('*.json')]


def quality_gate_compute(obj: dict[str,Any]) -> bool:
    try:
        spec=importlib.util.spec_from_file_location('quality_gate_v4_1', ROOT/'_shared/quality/quality_gate_v4_1.py')
        mod=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
        return bool(mod.compute_quality(obj).get('passed'))
    except Exception:
        return False

def check_manifests(paths: list[Path]) -> tuple[list[str],dict[str,Any]]:
    errors=[]; confirmed=0; checked=0
    qg=ROOT/'_shared/quality/quality_gate_v4_1.py'
    for p in paths:
        try: obj=load(p)
        except Exception: continue
        if not isinstance(obj,dict) or 'final_status' not in obj: continue
        checked+=1
        strict=validate(ROOT/'schemas/evidence_manifest.strict.schema.json', obj)
        errors += [f'{rel(p)} strict schema: {e}' for e in strict]
        for i,cl in enumerate(obj.get('report_claims') or []):
            if not cl.get('evidence_id'): errors.append(f'{rel(p)} report_claims[{i}] missing evidence_id')
        if obj.get('final_status')=='confirmed':
            confirmed+=1
            if not quality_gate_compute(obj): errors.append(f'{rel(p)} confirmed manifest failed quality_gate_v4_1')
    return errors, {'checked':checked,'confirmed':confirmed}

def check_hygiene() -> tuple[list[str],dict[str,Any]]:
    errors=[]
    bad=[]
    for p in ROOT.rglob('*'):
        name=p.name
        if p.is_dir() and name=='__pycache__': bad.append(rel(p))
        if p.is_file() and (name.endswith('.pyc') or name.endswith('.pyo') or name in {'CHANGELOG.md','VERSION.md'} or re.search(r'(RELEASE_NOTES|CLEANUP_REPORT|\.bak$|~$|tmp$)', name, re.I)):
            if '_shared/knowledge' in rel(p) or '_shared/vulnerability_templates' in rel(p): continue
            bad.append(rel(p))
    if bad: errors.append('package hygiene forbidden files: '+', '.join(bad[:30]))
    k=len([p for p in (ROOT/'_shared/knowledge').rglob('*') if p.is_file()]) if (ROOT/'_shared/knowledge').exists() else 0
    t=len([p for p in (ROOT/'_shared/vulnerability_templates').rglob('*') if p.is_file()]) if (ROOT/'_shared/vulnerability_templates').exists() else 0
    if k==0: errors.append('knowledge base missing')
    if t==0: errors.append('vulnerability templates missing')
    return errors, {'knowledge_files':k,'template_files':t,'forbidden_file_count':len(bad)}

def check_dashboard() -> tuple[list[str],dict[str,Any]]:
    errors=[]; details={}
    dash=ROOT/'_shared/dashboard/dashboard.html'
    if dash.exists():
        text=dash.read_text(encoding='utf-8',errors='ignore')
        if 'Local fixtures and optional local run manifests only' in text and 'fixture_only_not_proof' not in text:
            errors.append('dashboard.html is fixture-derived but lacks fixture_only_not_proof marker')
    return errors, details

def run_gate(cmd: list[str]) -> dict[str,Any]:
    cp=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    try: obj=json.loads(cp.stdout)
    except Exception: obj={'stdout':cp.stdout[-500:],'stderr':cp.stderr[-500:]}
    obj['returncode']=cp.returncode; return obj


def check_v3_p0_outputs(scan_dirs: list[str] | None) -> tuple[list[str], dict[str, Any]]:
    errors=[]; details={'checked_dirs':scan_dirs or []}
    required={
      '03b_js_dual_ast_sourcemap.json':'schemas/js_dual_ast_sourcemap.schema.json',
      '01b_parser_readiness.json':'schemas/parser_runtime_readiness.schema.json',
      '01c_external_parsers.json':'schemas/external_parser_extract.schema.json',
      '02b_authz_path_proof.json':'schemas/authz_path_proof.schema.json',
      '02c_interprocedural_dataflow.json':'schemas/interprocedural_dataflow.schema.json',
      '04c_tenant_object_binding.json':'schemas/tenant_object_binding.schema.json',
      '06b_performance_gate.json':'schemas/performance_gate.schema.json',
      '09b_playwright_multirole_replay.json':'schemas/dynamic_replay_execution.schema.json',
      '09c_graphql_replay.json':'schemas/dynamic_replay_execution.schema.json',
      '09d_websocket_replay.json':'schemas/dynamic_replay_execution.schema.json',
      '10_manifest_index.json':'schemas/manifest_index.schema.json'
    }
    for d in scan_dirs or []:
        base=Path(d)
        for name, schema in required.items():
            p=base/name
            if not p.exists():
                errors.append(f'missing P0 output {p}'); continue
            try: obj=load(p)
            except Exception as exc:
                errors.append(f'{p} parse failed: {exc}'); continue
            errors += [f'{rel(p)} schema: {e}' for e in validate(ROOT/schema,obj)]
            if name=='06b_performance_gate.json' and obj.get('passed') is not True:
                errors.append('performance gate failed')
            if name=='10_manifest_index.json' and any(x.get('fixture_allowed') is True for x in obj.get('manifests',[])):
                errors.append('manifest index default view includes fixtures')
    return errors, details

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default=str(ROOT)); ap.add_argument('--detector-output'); ap.add_argument('--manifest-dir',action='append'); ap.add_argument('--scan-output',action='append'); ap.add_argument('--out')
    a=ap.parse_args(); blockers=[]; sections={}
    for name,func in [('detectors',check_detectors),('hygiene',check_hygiene),('dashboard',check_dashboard)]:
        errs,det=func(); sections[name]=det; blockers += [f'{name}: {e}' for e in errs]
    errs,det=check_detector_output(a.detector_output); sections['detector_output']=det; blockers += [f'detector_output: {e}' for e in errs]
    mpaths=[]
    for d in a.manifest_dir or []: mpaths += manifest_paths(Path(d))
    errs,det=check_manifests(mpaths); sections['manifests']=det; blockers += [f'manifests: {e}' for e in errs]
    errs,det=check_v3_p0_outputs(a.scan_output); sections['v3_p0_outputs']=det; blockers += [f'v3_p0_outputs: {e}' for e in errs]
    for s in a.scan_output or []:
        sg=run_gate([sys.executable,'_shared/quality/secret_redaction_gate.py',s])
        sections.setdefault('secret_scans',[]).append(sg)
        if not sg.get('passed'): blockers.append(f'secret_redaction: {s} has {sg.get("finding_count")} findings')
    res={'schema_version':'reverse_acceptance_gate_v2','passed':not blockers,'blocker_count':len(blockers),'blockers':blockers[:200],'sections':sections,'policy':'No confirmed claim without strict manifest, dynamic evidence, role/tenant controls where applicable, evidence_id and second-pass redaction.'}
    text=json.dumps(res,ensure_ascii=False,indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(text+'\n',encoding='utf-8')
    print(text); return 0 if res['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
