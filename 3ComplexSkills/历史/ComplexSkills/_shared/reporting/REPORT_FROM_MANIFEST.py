#!/usr/bin/env python3
"""Template-specific evidence-driven report renderer v4.1.

Refuses generic confirmed reports. Every confirmed manifest must pass quality_gate_v4_1
and must bind report_renderer.template_id to a renderer under _shared/reporting/renderers/.
"""
from __future__ import annotations
import argparse, importlib.util, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
QG=ROOT/'_shared/quality/quality_gate_v4_1.py'
spec=importlib.util.spec_from_file_location('quality_gate_v4_1', QG); qg=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(qg)
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def esc(v): return str(v).replace('\n',' ')
def generate(m,q):
    tid=m.get('template_id'); rr=m.get('report_renderer') or {}; renderer=ROOT/(rr.get('renderer_path') or f'_shared/reporting/renderers/{tid}.md')
    if m.get('final_status')=='confirmed':
        if rr.get('template_id') != tid or rr.get('generic_renderer_forbidden') is not True or not renderer.exists():
            raise SystemExit('confirmed report requires matching template-specific renderer')
        if not str(m.get('evidence_id','')).startswith('EVID-'):
            raise SystemExit('confirmed report requires evidence_id')
    fields=((m.get('specialized_evidence') or {}).get('fields') or {})
    auth=m.get('auth_context') if isinstance(m.get('auth_context'),dict) else {}
    ten=m.get('tenant_context') if isinstance(m.get('tenant_context'),dict) else {}
    req=m.get('request_summary') if isinstance(m.get('request_summary'),dict) else {}
    resp=m.get('response_summary') if isinstance(m.get('response_summary'),dict) else {}
    neg=m.get('negative_control') or []
    blocked=[n for n in neg if isinstance(n,dict) and str(n.get('result','')).lower() in {'blocked','denied','rejected'}]
    lines=[
        f"# {tid} Security Finding: {m.get('candidate_id')}", '',
        '## Required traceability fields',
        f"- finding_id: `{m.get('candidate_id')}`",
        f"- detector_id: `{m.get('detector_id') or tid}`",
        f"- evidence_id: `{m.get('evidence_id')}`",
        f"- source_file: `{m.get('source_file')}`",
        f"- source_line: `{m.get('source_line')}`",
        f"- affected_route: `{m.get('method')} {m.get('route')}`",
        f"- affected_parameter: `{m.get('parameter')}`",
        f"- affected_role: `{auth.get('role') or m.get('affected_role') or 'unknown'}`",
        f"- affected_tenant: `{ten.get('target_tenant') or m.get('affected_tenant') or 'unknown'}`",
        f"- request_summary: `{esc(req)}`",
        f"- response_summary: `{esc(resp)}`",
        f"- validation_status: `{m.get('final_status')}`",
        f"- negative_control: `{esc(neg[:3])}`",
        f"- blocked_control: `{esc(blocked[:3])}`",
        f"- severity_reason: `{esc((m.get('impact') or {}).get('security_impact') if isinstance(m.get('impact'),dict) else m.get('impact'))}`",
        f"- confidence_reason: `quality_gate_passed={q.get('passed')} score={q.get('total')}`",
        f"- reproduction_scope: `{m.get('authorization_scope')}`",
        f"- non_destructive_note: `{esc(m.get('non_destructive_boundary'))}`",
        f"- limitations: `fixture_only_not_proof unless generated from a real authorized project manifest`",
        f"- remediation: `Apply template-specific fix and add regression coverage.`",
        '',
        f"- Renderer: {renderer.relative_to(ROOT) if renderer.exists() else 'missing'}",
        f"- Final status: {m.get('final_status')}",
        f"- Quality gate: passed={q.get('passed')} total={q.get('total')}",
        f"- Authorized scope: {m.get('authorization_scope')}",
        '', '## Route and object context',
        f"- Route: `{m.get('method')} {m.get('route')}`",
        f"- Parameter: `{m.get('parameter')}`",
        f"- Auth context: `{esc(m.get('auth_context'))}`",
        f"- Tenant context: `{esc(m.get('tenant_context'))}`",
        '', '## Template-specific evidence']
    for k,v in fields.items(): lines.append(f"- {k}: {esc(v)}")
    lines += ['', '## Evidence artifacts', f"- Code evidence count: {len(m.get('code_evidence') or [])}", f"- Dynamic evidence groups: {len(m.get('dynamic_evidence') or [])}", f"- Negative controls: {len(m.get('negative_control') or [])}", '', '## Non-destructive boundary', f"- {esc(m.get('non_destructive_boundary'))}", '', '## Quality gate hard blocks']
    for b in q.get('hard_blocks') or []: lines.append(f"- {b}")
    lines += ['', '## Remediation', 'Apply the template-specific fix and add positive/negative/blocked/review replay coverage.']
    return '\n'.join(lines)+'\n'
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('manifest'); ap.add_argument('-o','--output'); ap.add_argument('--allow-nonconfirmed',action='store_true'); a=ap.parse_args(); m=load(Path(a.manifest)); res=qg.compute_quality(m)
    if m.get('final_status')=='confirmed' and not res.get('passed'):
        print(json.dumps({'error':'refusing confirmed report because quality gate failed','quality_gate':res},ensure_ascii=False,indent=2),file=sys.stderr); return 1
    if m.get('final_status')!='confirmed' and not a.allow_nonconfirmed:
        print(json.dumps({'error':'non-confirmed report requires --allow-nonconfirmed','final_status':m.get('final_status'),'quality_gate':res},ensure_ascii=False,indent=2),file=sys.stderr); return 2
    out=generate(m,res)
    if a.output: Path(a.output).write_text(out,encoding='utf-8')
    else: print(out)
    return 0
if __name__=='__main__': raise SystemExit(main())
