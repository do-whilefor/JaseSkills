#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, tempfile, os, sys, signal
from pathlib import Path


PY = sys.executable
def run(cmd, cwd, timeout=45):
    kwargs={}
    if os.name == 'nt':
        kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs['start_new_session'] = True
    proc = subprocess.Popen(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    try:
        out, err = proc.communicate(timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        if os.name == 'nt':
            proc.kill()
        else:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except Exception:
                proc.kill()
        try:
            out, err = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill(); out, err = proc.communicate()
        rc = 124
        err = (err or '') + '\nTIMEOUT'
    return {"cmd":cmd,"returncode":rc,"stdout":out or '',"stderr":err or ''}

def write(p:Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')

def main():
    ap=argparse.ArgumentParser(description='Local unit tests for anti-hallucination, strict blocking, schema validation, and static-only detector behavior.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='tests/reverse-audit-last-run')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=(root/args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    tests=[]

    # Test 1: schema validator must fail invalid evidence manifest.
    bad=out/'bad_evidence_manifest.json'
    write(bad, {"schema_version":"js-evidence-manifest/v1","status":"ready","runtime_requirements":{},"artifacts":[]})
    r=run([PY,'scripts/js_schema_validator.py','--schema','schemas/js-evidence-manifest.schema.json','--input',str(bad)], root)
    tests.append({"name":"schema_validator_rejects_incomplete_evidence_manifest","ok":r['returncode']!=0,"returncode":r['returncode'],"stdout_tail":r['stdout'][-800:],"stderr_tail":r['stderr'][-800:]})

    # Test 2: static-only graph must not create confirmed even with a synthetic ready manifest.
    graph=out/'unit_static_graph.json'; ledger=out/'unit_ledger.json'; scope=out/'unit_scope.json'; manifest=out/'unit_manifest.json'; detector_out=out/'unit_detector'
    write(graph,{"schema_version":"js-semantic-graph/v1","static_only":True,"evidence":[{"kind":"api_call","endpoint":"/api/admin/users","file":"app.js","line":1,"value":"admin tenant role authorization"}]})
    write(ledger,{"schema_version":"js-top-tier-ledger/v1","evidence":[]})
    write(scope,{"authorized_use":True,"non_destructive":True,"targets":["fixtures"],"roles":["admin","user"],"tenants":["a","b"]})
    write(manifest,{"status":"ready","static_only":True,"items":[{"request":{},"response":{},"kind":"role-tenant-map","value":"role tenant"}]})
    r=run([PY,'scripts/js_detector_registry_runner.py','--graph',str(graph),'--ledger',str(ledger),'--scope',str(scope),'--manifest',str(manifest),'--out',str(detector_out)], root)
    produced=json.loads((detector_out/'js_detector_registry_run.json').read_text(encoding='utf-8')) if (detector_out/'js_detector_registry_run.json').exists() else {}
    tests.append({"name":"static_only_detector_never_confirms","ok":r['returncode']==0 and produced.get('summary',{}).get('confirmed')==0,"returncode":r['returncode'],"confirmed":produced.get('summary',{}).get('confirmed'),"stdout_tail":r['stdout'][-800:],"stderr_tail":r['stderr'][-800:]})

    # Test 3: strict quality gate must block non-top-tier report dirs.
    qdir=out/'unit_quality'
    qdir.mkdir(parents=True, exist_ok=True)
    r=run([PY,'scripts/js_top_tier_quality_gate.py','--report-dir',str(qdir),'--strict'], root)
    tests.append({"name":"strict_quality_gate_blocks_low_evidence","ok":r['returncode']!=0,"returncode":r['returncode'],"stdout_tail":r['stdout'][-800:],"stderr_tail":r['stderr'][-800:]})

    # Test 4: adversarial harness must produce zero confirmed statuses.
    adv=out/'unit_adversarial'
    r=run([PY,'scripts/js_adversarial_harness.py','--out',str(adv)], root)
    adv_obj=json.loads((adv/'js_adversarial_result.json').read_text(encoding='utf-8')) if (adv/'js_adversarial_result.json').exists() else {}
    tests.append({"name":"adversarial_harness_no_confirmed","ok":r['returncode']==0 and adv_obj.get('ok') is True and all(c.get('actual_status')!='confirmed' for c in adv_obj.get('cases',[])),"returncode":r['returncode'],"case_count":len(adv_obj.get('cases',[])),"stdout_tail":r['stdout'][-800:],"stderr_tail":r['stderr'][-800:]})



    # Test 5: runtime artifact importer must produce ready bundle on complete import sample.
    rt=out/'unit_runtime_import'
    r=run([PY,'scripts/js_runtime_artifact_importer.py','--evidence-root','fixtures/runtime-artifacts-import-sample','--out',str(rt)], root)
    rt_obj=json.loads((rt/'js_runtime_artifact_bundle.json').read_text(encoding='utf-8')) if (rt/'js_runtime_artifact_bundle.json').exists() else {}
    tests.append({"name":"runtime_artifact_importer_ready_on_complete_bundle","ok":r['returncode']==0 and rt_obj.get('status')=='ready' and all(rt_obj.get('requirements',{}).values()),"returncode":r['returncode'],"status":rt_obj.get('status'),"stdout_tail":r['stdout'][-800:],"stderr_tail":r['stderr'][-800:]})

    # Test 6: role/tenant authorization fixture must include positive, negative, and blocked outcomes.
    rtd=out/'unit_role_tenant'
    r=run([PY,'scripts/js_role_tenant_authorization_replay.py','--fixture-server','--port','8987','--out',str(rtd)], root)
    rtd_obj=json.loads((rtd/'js_role_tenant_authorization_result.json').read_text(encoding='utf-8')) if (rtd/'js_role_tenant_authorization_result.json').exists() else {}
    sm=rtd_obj.get('summary',{})
    tests.append({"name":"role_tenant_authorization_matrix_ready","ok":r['returncode']==0 and rtd_obj.get('status')=='ready' and sm.get('positive') and sm.get('negative') and sm.get('blocked'),"returncode":r['returncode'],"summary":sm,"stdout_tail":r['stdout'][-800:],"stderr_tail":r['stderr'][-800:]})

    # Test 7: hidden parameter acceptance fixture must include positive, negative, and blocked outcomes.
    hp=out/'unit_hidden_param'
    r=run([PY,'scripts/js_hidden_param_acceptance_matrix.py','--fixture-server','--port','8988','--out',str(hp)], root)
    hp_obj=json.loads((hp/'js_hidden_param_acceptance_matrix.json').read_text(encoding='utf-8')) if (hp/'js_hidden_param_acceptance_matrix.json').exists() else {}
    sm=hp_obj.get('summary',{})
    tests.append({"name":"hidden_param_acceptance_matrix_ready","ok":r['returncode']==0 and hp_obj.get('status')=='ready' and sm.get('positive') and sm.get('negative') and sm.get('blocked'),"returncode":r['returncode'],"summary":sm,"stdout_tail":r['stdout'][-800:],"stderr_tail":r['stderr'][-800:]})

    ok=all(t['ok'] for t in tests)
    res={"schema_version":"js-unit-tests/v1","ok":ok,"tests":tests,"summary":{"passed":sum(t['ok'] for t in tests),"failed":sum(not t['ok'] for t in tests)}}
    (out/'js_unit_tests.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({"ok":ok, **res['summary'], "out":str(out/'js_unit_tests.json')}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)
if __name__=='__main__': main()
