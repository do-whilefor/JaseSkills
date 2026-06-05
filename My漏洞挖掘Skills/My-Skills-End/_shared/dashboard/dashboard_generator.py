#!/usr/bin/env python3
from __future__ import annotations
import html, importlib.util, json, sys, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; SYSTEM_ROOT=ROOT.parent
spec=importlib.util.spec_from_file_location('quality_gate_v4_1', ROOT/'quality/quality_gate_v4_1.py'); qg=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(qg)
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def esc(x): return html.escape(str(x))
def sha(p):
    h=hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
def manifests():
    paths=list((ROOT/'tests/fixtures').glob('C[0-9][0-9]-*.json'))
    if (ROOT/'runs').exists(): paths += [p for p in (ROOT/'runs').rglob('*.json') if 'manifest' in p.name.lower() or 'evidence' in p.name.lower()]
    return sorted(set(paths))
def main():
    out=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'dashboard/dashboard.html'; rows=[]; status_counts={}; block_counts={}; template_counts={}
    for f in manifests():
        try: m=load(f)
        except Exception: continue
        if 'template_id' not in m: continue
        res=qg.compute_quality(m); status=m.get('final_status'); status_counts[status]=status_counts.get(status,0)+1; template_counts[m.get('template_id')]=template_counts.get(m.get('template_id'),0)+1
        for b in res.get('hard_blocks') or []: block_counts[b]=block_counts.get(b,0)+1
        dyn=len(m.get('dynamic_evidence') or []); code=len(m.get('code_evidence') or []); neg=len(m.get('negative_control') or []); specs=','.join(sorted(((m.get('specialized_evidence') or {}).get('fields') or {}).keys()))
        ledger=m.get('role_object_tenant_ledger') or {}; rr=m.get('report_renderer') or {}; taint=m.get('taint_review') or {}
        rows.append(f"<tr><td>{esc(f.relative_to(SYSTEM_ROOT))}<br><small>{sha(f)[:16]}</small></td><td>{esc(m.get('template_id'))}</td><td>{esc(m.get('method'))} {esc(m.get('route'))}</td><td>{esc(m.get('candidate_id'))}</td><td>code={code}<br>dynamic={dyn}<br>negative={neg}<br>specialized={esc(specs)}<br>ledger_complete={esc(ledger.get('complete'))}</td><td>{esc(res.get('schema_version'))}<br>{esc(res.get('total'))}<br>pass={esc(res.get('passed'))}<br>blocks={esc(','.join(res.get('hard_blocks') or []))}</td><td>{esc(rr.get('renderer_path') or m.get('report_template'))}<br>generic_forbidden={esc(rr.get('generic_renderer_forbidden'))}</td><td>{esc(taint.get('decision'))}</td><td>{esc(status)}</td></tr>")
    e2e=load(ROOT/'tests/e2e_replay/e2e_replay_index.json') if (ROOT/'tests/e2e_replay/e2e_replay_index.json').exists() else {}; queue=load(ROOT/'review_queue/queue.json') if (ROOT/'review_queue/queue.json').exists() else {}
    html_text=f"""<!doctype html><meta charset='utf-8'><title>Authorized Security Audit Dashboard v4.1</title><style>body{{font-family:system-ui,Arial,sans-serif;margin:24px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ccc;padding:6px;vertical-align:top}}pre{{white-space:pre-wrap;background:#f6f6f6;padding:8px}}</style><h1>Authorized Security Audit Dashboard v4.1</h1><p>Default schema: EVIDENCE_MANIFEST_SCHEMA.v4.1. Local fixtures and optional local run manifests only. No external target scanning.</p><h2>Route → Candidate → Evidence → Quality Gate → Report → Taint</h2><table><thead><tr><th>Manifest/hash</th><th>Template</th><th>Route</th><th>Candidate</th><th>Evidence + ledger</th><th>Quality gate</th><th>Renderer</th><th>Taint</th><th>Status</th></tr></thead><tbody>{''.join(rows)}</tbody></table><h2>Status counts</h2><pre>{esc(json.dumps(status_counts,ensure_ascii=False,indent=2))}</pre><h2>Hard blocks</h2><pre>{esc(json.dumps(block_counts,ensure_ascii=False,indent=2))}</pre><h2>Template counts</h2><pre>{esc(json.dumps(template_counts,ensure_ascii=False,indent=2))}</pre><h2>E2E exact replay samples</h2><pre>{esc(json.dumps(e2e,ensure_ascii=False,indent=2))}</pre><h2>Human review queue</h2><pre>{esc(json.dumps(queue,ensure_ascii=False,indent=2))}</pre>"""
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(html_text,encoding='utf-8'); print(out); return 0
if __name__=='__main__': raise SystemExit(main())
