#!/usr/bin/env python3
"""Adapter wrapper for a local JavaParser CLI jar.
Set JAVAPARSER_CLI=/path/to/javaparser-cli.jar. This wrapper never fabricates AST.
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--probe', action='store_true'); ap.add_argument('files', nargs='*')
    a=ap.parse_args(); jar=os.environ.get('JAVAPARSER_CLI')
    if not jar:
        print(json.dumps({'backend':'javaparser','runtime_ready':False,'reason':'JAVAPARSER_CLI not set'})); return 2 if a.probe else 0
    cmd=['java','-jar',jar] + (['--probe'] if a.probe else a.files)
    cp=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
    if a.probe:
        print(cp.stdout or cp.stderr); return cp.returncode
    try: obj=json.loads(cp.stdout)
    except Exception: obj={'backend':'javaparser','parser_confidence':'full_ast','raw_stdout':cp.stdout[-2000:],'stderr':cp.stderr[-1000:]}
    print(json.dumps(obj, ensure_ascii=False, indent=2)); return cp.returncode
if __name__=='__main__': raise SystemExit(main())
