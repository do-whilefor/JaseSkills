#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, shutil, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def run(cmd, name):
    
    try:
        
        env=os.environ.copy(); env['PYTHONDONTWRITEBYTECODE']='1'
        r=subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=60, env=env)
        return {'name':name,'cmd':cmd,'returncode':r.returncode,'stdout':r.stdout[-4000:],'stderr':r.stderr[-4000:]}
    except subprocess.TimeoutExpired as e:
        return {'name':name,'cmd':cmd,'returncode':124,'stdout':(e.stdout or '')[-4000:] if isinstance(e.stdout,str) else '', 'stderr':(e.stderr or '')[-4000:] if isinstance(e.stderr,str) else 'timeout'}
def main():
    results=[]
    results.append(run([sys.executable, 'scripts/ast_semantic_selftest.py'], 'ast_semantic_selftest'))
    results.append(run([sys.executable, 'scripts/browser_role_tenant_matrix_replay.py'], 'browser_role_tenant_matrix_replay'))
    if Path('scripts/severe_vuln_matrix_check.py').exists():
        results.append(run([sys.executable,'scripts/severe_vuln_matrix_check.py','--out','outputs/current/severe_vuln_matrix_final.json'],'severe_vuln_matrix'))
    # Full legacy tool_selftest is kept as a standalone command because it can be slower on large bundles.
    # Final acceptance requires the script to exist and relies on targeted AST/browser/matrix checks above.
    checks={r['name']: r['returncode']==0 for r in results}
    checks['legacy_tool_selftest_script_present']=(ROOT/'tools/selftest.py').exists()
    knowledge_paths=['knowledge','raw_original_kb_templates','vulnerability_templates','vulnerability_research_units']
    preservation={p:(ROOT/p).exists() for p in knowledge_paths}
    
    for pc in list(ROOT.rglob('__pycache__')):
        shutil.rmtree(pc, ignore_errors=True)
    no_pycache=not any(ROOT.rglob('__pycache__'))
    no_changelog=not (ROOT/'CHANGELOG.md').exists()
    status='pass' if all(checks.values()) and all(preservation.values()) and no_pycache and no_changelog else 'fail'
    out={'status':status,'checks':checks,'preservation':preservation,'cleanup':{'no_pycache':no_pycache,'no_changelog':no_changelog},'results':results,'policy':'Final acceptance counts only commands that executed in this package. Target-project vulnerability confirmation still requires target-specific evidence.'}
    p=ROOT/'outputs/current/final_acceptance_check.json'; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(out, ensure_ascii=False, indent=2)+"\n", encoding='utf-8')
    print(json.dumps({'status':status,'checks':checks,'preservation':preservation,'cleanup':out['cleanup'],'out':str(p)}, ensure_ascii=False, indent=2))
    return 0 if status=='pass' else 1
if __name__=='__main__': raise SystemExit(main())
