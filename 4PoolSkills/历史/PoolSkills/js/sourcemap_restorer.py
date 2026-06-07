#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, json, re, sys
from pathlib import Path
VLQ_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
VLQ = {c:i for i,c in enumerate(VLQ_CHARS)}

def _decode_vlq(seg: str):
    vals=[]; value=0; shift=0
    for ch in seg:
        digit=VLQ[ch]; cont=digit & 32; digit &= 31
        value += digit << shift
        if cont:
            shift += 5
        else:
            sign=value & 1
            vals.append(-(value >> 1) if sign else (value >> 1))
            value=0; shift=0
    return vals

def decode_mappings(mappings: str):
    rows=[]; src=0; src_line=0; src_col=0; name=0
    for gen_line, line in enumerate(mappings.split(';'), start=1):
        gen_col=0; row=[]
        for seg in filter(None, line.split(',')):
            vals=_decode_vlq(seg)
            if not vals: continue
            gen_col += vals[0]
            rec={'generated_line':gen_line,'generated_col':gen_col}
            if len(vals) >= 4:
                src += vals[1]; src_line += vals[2]; src_col += vals[3]
                rec.update({'source_index':src,'source_line':src_line+1,'source_col':src_col})
            if len(vals) >= 5:
                name += vals[4]; rec['name_index']=name
            row.append(rec)
        rows.append(row)
    return rows

def _map_from_js(js_path: Path) -> Path | None:
    text=js_path.read_text(encoding='utf-8',errors='ignore')[-2000:]
    m=re.search(r'sourceMappingURL=([^\s*]+)', text)
    if not m: return None
    url=m.group(1).strip()
    if url.startswith('data:application/json'):
        marker='base64,'
        if marker in url:
            data=base64.b64decode(url.split(marker,1)[1]).decode('utf-8','replace')
            out=js_path.with_suffix(js_path.suffix+'.inline.map')
            out.write_text(data,encoding='utf-8')
            return out
    p=(js_path.parent/url).resolve()
    return p if p.exists() else None

def restore(js_file: str | Path | None = None, map_file: str | Path | None = None, out_dir: str | Path | None = None) -> dict:
    js_path=Path(js_file).resolve() if js_file else None
    mp=Path(map_file).resolve() if map_file else (_map_from_js(js_path) if js_path else None)
    if not mp or not mp.exists():
        return {'schema_version':'sourcemap-restore-v1','status':'failed','error':'source_map_not_found','restored_sources':[]}
    data=json.loads(mp.read_text(encoding='utf-8',errors='ignore'))
    out=Path(out_dir or (mp.parent/'restored_sources')).resolve(); out.mkdir(parents=True,exist_ok=True)
    sources=data.get('sources') or []
    contents=data.get('sourcesContent') or []
    restored=[]
    for i, src in enumerate(sources):
        content=contents[i] if i < len(contents) and contents[i] is not None else ''
        safe=re.sub(r'[^A-Za-z0-9_.-]+','_',src).strip('_') or f'source_{i}.txt'
        fp=out/safe
        fp.parent.mkdir(parents=True,exist_ok=True)
        fp.write_text(content,encoding='utf-8')
        restored.append({'source':src,'restored_path':str(fp),'bytes':len(content.encode())})
    mappings=decode_mappings(data.get('mappings','')) if data.get('mappings') else []
    manifest={'schema_version':'sourcemap-restore-v1','status':'parsed','map_file':str(mp),'source_root':data.get('sourceRoot'),'restored_sources':restored,'mapping_rows':len(mappings),'mapping_segments':sum(len(r) for r in mappings)}
    (out/'sourcemap_restore_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--js-file'); ap.add_argument('--map-file'); ap.add_argument('--out-dir',required=True); ap.add_argument('--out'); ns=ap.parse_args()
    data=restore(ns.js_file, ns.map_file, ns.out_dir)
    if ns.out:
        Path(ns.out).parent.mkdir(parents=True,exist_ok=True); Path(ns.out).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':data.get('status'),'restored':len(data.get('restored_sources',[]))},ensure_ascii=False)); sys.exit(0 if data.get('status')=='parsed' else 1)
if __name__=='__main__': main()
