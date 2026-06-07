#!/usr/bin/env python3
"""Execute full external parser adapters only when their runtime probes passed."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[3]
BACK=Path(__file__).resolve().parent/'parser_backends'
EXT={'.java':'java','.php':'php','.go':'go','.rb':'ruby','.rs':'rust'}
SKIP={'.git','node_modules','vendor','__pycache__','.venv','target','build'}

def load_json_stdout(cmd):
    cp=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,cwd=ROOT)
    try: obj=json.loads(cp.stdout or '{}')
    except Exception: obj={'parse_error':True,'stdout_tail':cp.stdout[-1200:],'stderr_tail':cp.stderr[-1200:]}
    obj['returncode']=cp.returncode
    return obj

def iter_lang_files(project: Path, lang: str):
    return [p for p in project.rglob('*') if p.is_file() and EXT.get(p.suffix.lower())==lang and not any(part in SKIP for part in p.relative_to(project).parts)]

def build(project: Path) -> dict[str,Any]:
    readiness=load_json_stdout([sys.executable, str(BACK/'parser_runtime_manager.py')])
    extracts=[]
    lang_rows={x.get('language'):x for x in readiness.get('languages',[]) if isinstance(x,dict)}
    for lang,row in lang_rows.items():
        if lang not in {'java','php','go','ruby','rust'}: continue
        files=iter_lang_files(project, lang)
        rec={'language':lang,'runtime_ready':bool(row.get('runtime_ready')),'file_count':len(files),'executed':False,'parser_confidence':'manual_required','promotion_status':row.get('promotion_status'),'rows':[]}
        if row.get('runtime_ready') and files:
            if lang=='go': cmd=['go','run',str(BACK/'go_parser_bridge.go')]+[str(p) for p in files]
            elif lang=='ruby': cmd=['ruby',str(BACK/'ruby_ripper_bridge.rb')]+[str(p) for p in files]
            elif lang=='php': cmd=['php',str(BACK/'php_parser_bridge.php')]+[str(p) for p in files]
            elif lang=='java': cmd=[sys.executable,str(BACK/'java_javaparser_bridge.py')]+[str(p) for p in files]
            elif lang=='rust': cmd=['cargo','run','--quiet','--manifest-path',str(BACK/'rust_syn_bridge/Cargo.toml'),'--']+[str(p) for p in files]
            out=load_json_stdout(cmd); rec.update({'executed': out.get('returncode')==0, 'parser_confidence':'full_ast' if out.get('returncode')==0 else 'manual_required', 'rows':out.get('files') or [], 'adapter_output':out})
        extracts.append(rec)
    return {'schema_version':'external_parser_extract_v1','project_root':str(project),'readiness':readiness,'extracts':extracts,'promotion_policy':'Only executed=true and parser_confidence=full_ast rows may satisfy full-AST claims; otherwise code graph fallback remains candidate-only.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--out'); ap.add_argument('--validate', action='store_true')
    a=ap.parse_args(); obj=build(Path(a.project).resolve())
    if a.validate:
        try:
            import jsonschema
            schema=json.loads((ROOT/'schemas/external_parser_extract.schema.json').read_text())
            errs=[e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(obj)]
            if errs: obj['schema_errors']=errs
        except Exception as exc: obj['schema_errors']=[f'jsonschema_unavailable:{exc}']
    text=json.dumps(obj, ensure_ascii=False, indent=2)
    if a.out: Path(a.out).parent.mkdir(parents=True, exist_ok=True); Path(a.out).write_text(text+'\n', encoding='utf-8')
    else: print(text)
    return 0 if not obj.get('schema_errors') else 1
if __name__=='__main__': raise SystemExit(main())
