#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, argparse
from pathlib import Path
try:
    import yaml
except Exception:
    yaml=None
ROOT=Path(__file__).resolve().parents[1]

def run(cmd, expect_zero=True):
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    ok=(p.returncode==0) if expect_zero else (p.returncode!=0)
    return {'cmd':' '.join(map(str,cmd)),'returncode':p.returncode,'ok':ok,'stdout':p.stdout[-1000:],'stderr':p.stderr[-1000:]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',default='outputs/current/tool_registry_selftest_result.json'); ns=ap.parse_args()
    data={'ok':False,'registry_loaded':False,'registered_tools':0,'commands':[],'errors':[]}
    if not yaml:
        data['errors'].append('pyyaml_missing')
    else:
        reg=yaml.safe_load((ROOT/'tools/tool_registry.yaml').read_text(encoding='utf-8'))
        tools=reg.get('tools') or {}
        data['registry_loaded']=True; data['registered_tools']=len(tools)
        for name,spec in tools.items():
            for field in ['executable','category','requires_network','output_kind']:
                if field not in spec:
                    data['errors'].append(f'{name}:missing_{field}')
    data['commands'].append(run([sys.executable,'tools/tool_orchestrator.py','--root',str(ROOT),'--tool','python-version','--out','outputs/current/tool_registry_python_version.json'], True))
    data['commands'].append(run([sys.executable,'tools/tool_orchestrator.py','--root',str(ROOT),'--tool','definitely-not-registered','--out','outputs/current/tool_registry_unavailable.json'], False))
    unavailable=json.loads((ROOT/'outputs/current/tool_registry_unavailable.json').read_text(encoding='utf-8'))
    if unavailable.get('status')!='unavailable' or unavailable.get('result_is_success') is not False:
        data['errors'].append('unavailable_tool_not_marked_failure')
    data['ok']=data['registry_loaded'] and data['registered_tools']>=20 and not data['errors'] and all(c['ok'] for c in data['commands'])
    out=ROOT/ns.out; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'ok':data['ok'],'registered_tools':data['registered_tools'],'errors':data['errors']},ensure_ascii=False))
    sys.exit(0 if data['ok'] else 1)
if __name__=='__main__': main()
