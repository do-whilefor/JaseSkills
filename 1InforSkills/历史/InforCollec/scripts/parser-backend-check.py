#!/usr/bin/env python3
"""Parser backend availability checker.

This prevents the package from pretending AST/dataflow support is runtime-ready
when the local backend is absent. It checks tools/imports only; it does not
install anything and does not execute target project code.
"""
from __future__ import annotations
import argparse, importlib.util, json, shutil, subprocess, sys
from datetime import datetime, timezone

def cmd_version(cmd:list[str], timeout:int=5):
    exe=shutil.which(cmd[0])
    if not exe: return {'available':False,'reason':'not_on_path'}
    try:
        r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=timeout)
        return {'available':r.returncode==0,'path':exe,'version':(r.stdout or '').strip().split('\n')[0][:200],'returncode':r.returncode}
    except Exception as e: return {'available':False,'path':exe,'reason':type(e).__name__+': '+str(e)}

def py_import(name:str):
    return {'available': importlib.util.find_spec(name) is not None}

def node_require(pkg:str):
    if not shutil.which('node'): return {'available':False,'reason':'node_not_on_path'}
    code=f"try{{require.resolve('{pkg}'); console.log('ok')}}catch(e){{process.exit(2)}}"
    try:
        r=subprocess.run(['node','-e',code],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=5)
        return {'available':r.returncode==0,'returncode':r.returncode,'output':(r.stdout or '').strip()[:200]}
    except Exception as e: return {'available':False,'reason':type(e).__name__+': '+str(e)}

def main():
    ap=argparse.ArgumentParser(description='Check parser backend availability without installing dependencies.')
    ap.add_argument('--require', action='append', default=[], help='Backend names that must be available or exit non-zero')
    ap.add_argument('--out', default=None)
    args=ap.parse_args()
    checks={
      'python_ast': {'available': True, 'module':'ast', 'runtime':sys.version.split()[0]},
      'python_libcst': py_import('libcst'),
      'python_tree_sitter': py_import('tree_sitter'),
      'node': cmd_version(['node','--version']),
      'npm': cmd_version(['npm','--version']),
      'typescript_compiler_api': node_require('typescript'),
      'babel_parser': node_require('@babel/parser'),
      'acorn': node_require('acorn'),
      'esprima': node_require('esprima'),
      'playwright_node': node_require('playwright'),
      'javaparser_cli_or_java': cmd_version(['java','-version']),
      'php': cmd_version(['php','-v']),
      'ruby_ripper': cmd_version(['ruby','-rripper','-e','puts Ripper.respond_to?(:sexp)']),
      'go_parser_toolchain': cmd_version(['go','version']),
      'rust_syn_toolchain': cmd_version(['cargo','--version']),
      'tree_sitter_cli': cmd_version(['tree-sitter','--version'])
    }
    missing=[r for r in args.require if not checks.get(r,{}).get('available')]
    report={'schema_version':'package-schema','generated_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'required_missing':missing,'status':'FAIL' if missing else 'PASS'}
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if args.out: open(args.out,'w',encoding='utf-8').write(text)
    print(text)
    return 2 if missing else 0
if __name__=='__main__': raise SystemExit(main())
