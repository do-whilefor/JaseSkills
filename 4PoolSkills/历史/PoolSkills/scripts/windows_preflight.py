#!/usr/bin/env python3
from __future__ import annotations
import json, os, platform, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TOOLS=['python','node','npm','php','composer','cargo','rustc','go','ruby','java','javac']

def version(cmd):
    exe=shutil.which(cmd)
    if not exe: return {'tool':cmd,'available':False,'path':None,'version':None}
    args=[exe,'--version'] if cmd not in {'java','javac'} else [exe,'-version']
    try:
        p=subprocess.run(args,capture_output=True,text=True,timeout=8)
        v=(p.stdout or p.stderr).splitlines()[0] if (p.stdout or p.stderr) else ''
        return {'tool':cmd,'available':True,'path':exe,'version':v,'exit_code':p.returncode}
    except Exception as e:
        return {'tool':cmd,'available':True,'path':exe,'version':None,'error':str(e)}

def main():
    checks=[version(t) for t in TOOLS]
    data={'schema_version':'windows-preflight-v1','platform':platform.platform(),'is_windows':platform.system().lower()=='windows','python':sys.version,'cwd':str(Path.cwd()),'root':str(ROOT),'tools':checks,'policy':'Missing optional parsers make related language findings candidate-only; tool absence is not success.'}
    out=ROOT/'outputs'/'current'/'windows_preflight.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'is_windows':data['is_windows'],'available_tools':sum(1 for x in checks if x['available'])},ensure_ascii=False))
if __name__=='__main__': main()
