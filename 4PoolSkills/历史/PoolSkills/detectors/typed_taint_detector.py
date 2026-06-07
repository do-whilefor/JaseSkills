#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from detectors.detector_runner import make_finding

def _fid(path): return 'finding-taint-'+hashlib.sha256(json.dumps(path,sort_keys=True).encode()).hexdigest()[:14]

def map_sink_to_detector(label: str) -> dict:
    low=(label or '').lower()
    if 'command' in low or 'eval' in low: return {'id':'command_injection','title':'User-controlled source reaches command/eval sink','severity_candidate':'high','requires_role_tenant':False}
    if 'sql' in low or 'nosql' in low or 'query' in low: return {'id':'sql_nosql_injection','title':'User-controlled source reaches query sink','severity_candidate':'high','requires_role_tenant':False}
    if 'file' in low: return {'id':'path_traversal','title':'User-controlled source reaches file sink','severity_candidate':'high','requires_role_tenant':False}
    if 'ssrf' in low or 'http' in low: return {'id':'ssrf','title':'User-controlled source reaches outbound HTTP sink','severity_candidate':'high','requires_role_tenant':False}
    return {'id':'generic_source_sink','title':'User-controlled source reaches sensitive sink','severity_candidate':'medium','requires_role_tenant':False}

def detect(taint_file: str | Path, out: str | Path | None = None) -> dict:
    data=json.loads(Path(taint_file).read_text(encoding='utf-8'))
    findings=[]
    for p in data.get('paths',[]):
        if p.get('sanitized'): continue
        sink=(p.get('nodes') or [{}])[-1]
        rule=map_sink_to_detector(sink.get('label') or sink.get('type'))
        line=sink.get('line') or 1; file=sink.get('file') or '<graph>'
        f=make_finding(rule,_fid(p),Path('.').resolve(),file,line,'cross_file_dataflow',sink.get('label') or 'sink', 'typed taint path', dataflow=p.get('nodes'))
        f['source']='typed_taint_dataflow'; f['confidence']='high'; f['taint_context']=p.get('context',[])
        findings.append(f)
    result={'schema_version':'finding-candidates-v1','findings':findings,'summary':{'findings':len(findings),'policy':'typed taint findings remain candidate until dynamic evidence is stitched'}}
    if out:
        Path(out).parent.mkdir(parents=True,exist_ok=True); Path(out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--taint',required=True); ap.add_argument('--out',required=True); ns=ap.parse_args(); data=detect(ns.taint,ns.out); print(json.dumps(data['summary'],ensure_ascii=False))
if __name__=='__main__': main()
