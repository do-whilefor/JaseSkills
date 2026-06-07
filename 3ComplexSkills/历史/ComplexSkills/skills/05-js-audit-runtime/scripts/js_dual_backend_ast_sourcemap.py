#!/usr/bin/env python3
"""Dual TypeScript/Babel AST bridge plus precise sourcemap VLQ decoder.

This is read-only and local. It only marks a backend ready when the runtime package
actually executed. Heuristic fallback rows remain candidate-only and cannot satisfy
confirmed proof requirements.
"""
from __future__ import annotations
import argparse, base64, json, os, re, subprocess, sys
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = Path(__file__).resolve().parent
B64 = {c:i for i,c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/')}
SKIP = {'.git','node_modules','vendor','__pycache__','.venv','dist','.next','.nuxt'}

def run_node(script: Path, project: Path) -> dict[str, Any]:
    if not script.exists():
        return {'ready': False, 'backend': script.stem, 'reason': 'script_missing'}
    try:
        cp = subprocess.run(['node', str(script), str(project)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
        obj = json.loads(cp.stdout or '{}')
        obj.setdefault('backend', script.stem)
        obj['returncode'] = cp.returncode
        if cp.stderr and not obj.get('reason'): obj['stderr_tail'] = cp.stderr[-800:]
        return obj
    except FileNotFoundError:
        return {'ready': False, 'backend': script.stem, 'reason': 'node_not_found'}
    except Exception as exc:
        return {'ready': False, 'backend': script.stem, 'reason': f'{exc.__class__.__name__}: {exc}'}

def vlq_decode_segment(seg: str) -> list[int]:
    vals=[]; value=0; shift=0
    for ch in seg:
        digit=B64.get(ch)
        if digit is None: break
        cont=digit & 32; digit &= 31
        value += digit << shift
        if cont:
            shift += 5; continue
        sign=value & 1; num=value >> 1
        vals.append(-num if sign else num)
        value=0; shift=0
    return vals

def decode_map(path: Path, root: Path) -> dict[str, Any]:
    try: sm=json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    except Exception as exc: return {'map_file': str(path.relative_to(root)), 'parse_error': str(exc)}
    sources=sm.get('sources') or []
    mappings=sm.get('mappings') or ''
    gen_line=1; prev=[0,0,0,0,0]; rows=[]; source_hits={}
    for line in mappings.split(';'):
        gen_col=0
        for seg in [s for s in line.split(',') if s]:
            vals=vlq_decode_segment(seg)
            if not vals: continue
            gen_col += vals[0]
            row={'generated_line':gen_line,'generated_column':gen_col,'segment':seg}
            if len(vals)>=4:
                prev[1]+=vals[1]; prev[2]+=vals[2]; prev[3]+=vals[3]
                src=sources[prev[1]] if 0 <= prev[1] < len(sources) else '<source-index-out-of-range>'
                row.update({'source':src,'original_line':prev[2]+1,'original_column':prev[3]})
                source_hits[src]=source_hits.get(src,0)+1
            if len(vals)>=5:
                prev[4]+=vals[4]; row['name_index']=prev[4]
            if len(rows)<5000: rows.append(row)
        gen_line += 1
    return {'map_file': str(path.relative_to(root)), 'version': sm.get('version'), 'sources_count': len(sources), 'names_count': len(sm.get('names') or []), 'decoded_segment_count': len(rows), 'decoded_segments_sample': rows[:200], 'source_hit_counts': source_hits, 'sources_content_present': bool(sm.get('sourcesContent'))}

def walk_files(root: Path):
    for p in root.rglob('*'):
        if not p.is_file(): continue
        if any(part in SKIP for part in p.relative_to(root).parts): continue
        yield p

def heuristic(project: Path) -> dict[str, Any]:
    api=[]; dyn=[]; wrappers=[]; lazy=[]; routes=[]
    api_re=re.compile(r"\b(fetch|axios\.(?:get|post|put|patch|delete)|request|client\.(?:get|post)|api\.(?:get|post))\s*\(([^)]{0,200})", re.I)
    dyn_re=re.compile(r"import\s*\(\s*['\"]([^'\"]+)['\"]\s*\)")
    route_re=re.compile(r"\b(app|router)\.(get|post|put|patch|delete|options|head)\s*\(\s*['\"]([^'\"]+)['\"]", re.I)
    func_re=re.compile(r"function\s+([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{(.{0,1000})", re.S)
    for p in walk_files(project):
        if p.suffix.lower() not in {'.js','.jsx','.ts','.tsx','.mjs','.cjs'}: continue
        rel=str(p.relative_to(project)); txt=p.read_text(encoding='utf-8', errors='ignore')
        for m in api_re.finditer(txt): api.append({'file':rel,'line':txt[:m.start()].count('\n')+1,'client':m.group(1),'target':m.group(2)[:160],'parser':'heuristic_candidate'})
        for m in dyn_re.finditer(txt): dyn.append({'file':rel,'line':txt[:m.start()].count('\n')+1,'module':m.group(1),'parser':'heuristic_candidate'})
        for m in route_re.finditer(txt): routes.append({'file':rel,'line':txt[:m.start()].count('\n')+1,'method':m.group(2).upper(),'route':m.group(3),'parser':'heuristic_candidate'})
        for m in func_re.finditer(txt):
            if re.search(r"fetch\(|axios\.|request\(", m.group(2)): wrappers.append({'file':rel,'line':txt[:m.start()].count('\n')+1,'name':m.group(1),'wraps':'network_client','parser':'heuristic_candidate'})
        if re.search(r"webpackChunk|__webpack_require__|vite/preload-helper|lazy\(|React\.lazy", txt): lazy.append({'file':rel,'reason':'bundler_or_lazy_runtime_signal','parser':'heuristic_candidate'})
    return {'api_clients':api,'dynamic_imports':dyn,'wrapper_apis':wrappers,'lazy_chunks':lazy,'route_mappings':routes}

def merge_unique(*lists):
    out=[]; seen=set()
    for arr in lists:
        for x in arr or []:
            k=json.dumps(x, sort_keys=True, ensure_ascii=False)[:1000]
            if k in seen: continue
            seen.add(k); out.append(x)
    return out

def build(project: Path) -> dict[str, Any]:
    ts=run_node(SCRIPTS/'js_ts_ast_extractor.js', project)
    babel=run_node(SCRIPTS/'js_babel_ast_extractor.js', project)
    heur=heuristic(project)
    maps=[decode_map(p, project) for p in walk_files(project) if p.suffix=='.map' or p.name.endswith('.js.map')]
    backs=[]
    for obj,name in [(ts,'typescript_compiler_api'),(babel,'babel_parser')]:
        backs.append({'backend': obj.get('backend') or name, 'ready': bool(obj.get('ready')), 'claim_verified': bool(obj.get('ready') and obj.get('returncode',0)==0), 'reason': obj.get('reason') or obj.get('error') or obj.get('runtime_reason','')})
    ready=sum(1 for b in backs if b['claim_verified'])
    def get(obj, key): return obj.get(key) if isinstance(obj, dict) else []
    return {'schema_version':'js_dual_ast_sourcemap_v1','project_root':str(project),'backends':backs,'ready_backend_count':ready,'files_scanned':sum(1 for p in walk_files(project) if p.suffix.lower() in {'.js','.jsx','.ts','.tsx','.mjs','.cjs'}),'sourcemaps':maps,'dynamic_imports':merge_unique(get(ts,'dynamic_imports'),get(babel,'dynamic_imports'),heur['dynamic_imports']),'lazy_chunks':heur['lazy_chunks'],'api_clients':merge_unique(get(ts,'api_clients'),get(babel,'api_clients'),heur['api_clients']),'wrapper_apis':merge_unique(get(ts,'wrapper_apis'),get(babel,'wrapper_apis'),heur['wrapper_apis']),'route_mappings':merge_unique(get(ts,'routes'),get(babel,'routes'),heur['route_mappings']),'graphql':merge_unique(get(ts,'graphql'),get(babel,'graphql')),'websocket':merge_unique(get(ts,'realtime'),get(babel,'websocket')),'precision_policy':'Only rows from a ready backend are AST evidence; heuristic rows and sourcemap sourcesContent are candidate-only and require dynamic proof before confirmed.'}

def validate(obj):
    try:
        import jsonschema
        schema=json.loads((ROOT/'schemas/js_dual_ast_sourcemap.schema.json').read_text())
        return [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(obj)]
    except Exception as exc: return [f'jsonschema_unavailable:{exc}']

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--out'); ap.add_argument('--validate', action='store_true')
    a=ap.parse_args(); obj=build(Path(a.project).resolve())
    if a.validate:
        errs=validate(obj)
        if errs: obj['schema_errors']=errs
    text=json.dumps(obj, ensure_ascii=False, indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(text+'\n', encoding='utf-8')
    else: print(text)
    return 0 if not obj.get('schema_errors') else 1
if __name__=='__main__': raise SystemExit(main())
