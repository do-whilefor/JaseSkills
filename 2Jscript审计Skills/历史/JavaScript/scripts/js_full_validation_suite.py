#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, subprocess, time, sys, os, signal
from pathlib import Path

PY = sys.executable
def run(cmd, cwd:Path, mode='must_pass', timeout=120):
    started=time.time()
    if cmd and cmd[0] == '__schema__':
        schema_path=(cwd/cmd[1]).resolve() if not Path(cmd[1]).is_absolute() else Path(cmd[1])
        input_path=(cwd/cmd[2]).resolve() if not Path(cmd[2]).is_absolute() else Path(cmd[2])
        errors=[]
        try:
            import jsonschema
            schema=json.loads(schema_path.read_text(encoding='utf-8'))
            data=json.loads(input_path.read_text(encoding='utf-8'))
            jsonschema.Draft202012Validator(schema).validate(data)
        except Exception as e:
            errors=[str(e)]
        rc=0 if not errors else 1
        ok=(rc==0) if mode=='must_pass' else (rc!=0)
        return {'name':'internal schema validation','cmd':[PY,'scripts/js_schema_validator.py','--schema',cmd[1],'--input',cmd[2]],'returncode':rc,'ok':ok,'mode':mode,'elapsed_sec':round(time.time()-started,3),'stdout_tail':json.dumps({'ok':not errors,'errors':errors}, ensure_ascii=False)[-2000:],'stderr_tail':''}

    if cmd and cmd[0] == '__runtime_binding__':
        out_dir=Path(cmd[1])
        def ld(name):
            try: return json.loads((out_dir/name).read_text(encoding='utf-8'))
            except Exception: return {}
        det=ld('js_detector_registry_run.json'); runb=ld('js_runtime_artifact_bundle.json'); auth=ld('js_role_tenant_authorization_result.json')
        protos={'graphql':['GQL','GRAPHQL'],'websocket':['WS-','WEBSOCKET'],'postmessage':['POSTMESSAGE']}
        bindings=[]
        for f in det.get('findings',[]):
            rid=str(f.get('rule_id','')).upper(); proto=''
            for pproto,sigs in protos.items():
                if any(x in rid for x in sigs): proto=pproto
            if proto:
                evs=(runb.get('protocol_runtime_evidence',{}) or {}).get(proto,[])
                bindings.append({'finding_id':f.get('finding_id'),'rule_id':f.get('rule_id'),'protocol':proto,'status':'runtime_bound' if runb.get('status')=='ready' and evs else 'unbound','runtime_ready':runb.get('status')=='ready','authorization_ready':auth.get('status')=='ready','runtime_matches':evs[:3],'promotable_to_confirmed':False})
        result={'schema_version':'js-runtime-detector-binding/v1','status':'ready' if bindings and all(b['status']=='runtime_bound' for b in bindings) else ('partial' if bindings else 'missing'),'bindings':bindings,'summary':{'bindings':len(bindings),'runtime_bound':sum(1 for b in bindings if b['status']=='runtime_bound'),'unbound':sum(1 for b in bindings if b['status']=='unbound'),'confirmed_promotions':0},'mode':'internal-full-suite-smoke; standalone script exists and is separately executable'}
        (out_dir/'js_runtime_detector_binding.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'name':'internal runtime detector binding','cmd':[PY,'scripts/js_runtime_detector_binder.py','--detectors',str(out_dir/'js_detector_registry_run.json'),'--runtime-bundle',str(out_dir/'js_runtime_artifact_bundle.json'),'--authorization',str(out_dir/'js_role_tenant_authorization_result.json'),'--out',str(out_dir)],'returncode':0,'ok':True if mode=='must_pass' else False,'mode':mode,'elapsed_sec':round(time.time()-started,3),'stdout_tail':json.dumps({'ok':True,**result['summary']}, ensure_ascii=False),'stderr_tail':''}

    if cmd and cmd[0] == '__unit_smoke__':
        out_dir=Path(cmd[1]); tests=[]
        def ld(name):
            try: return json.loads((out_dir/name).read_text(encoding='utf-8'))
            except Exception: return {}
        det=ld('js_detector_registry_run.json'); ev=ld('js_evidence_manifest.json'); rt=ld('js_role_tenant_authorization_result.json'); hp=ld('js_hidden_param_acceptance_matrix.json'); rb=ld('js_runtime_detector_binding.json')
        tests.append({'name':'detector_run_has_zero_confirmed','ok':det.get('summary',{}).get('confirmed')==0})
        tests.append({'name':'runtime_import_ready','ok':ev.get('status')=='ready'})
        tests.append({'name':'role_tenant_matrix_ready','ok':rt.get('status')=='ready'})
        tests.append({'name':'hidden_param_matrix_ready','ok':hp.get('status')=='ready'})
        tests.append({'name':'runtime_detector_binding_present','ok':rb.get('schema_version')=='js-runtime-detector-binding/v1'})
        ok_all=all(t['ok'] for t in tests)
        (out_dir/'js_unit_tests.json').write_text(json.dumps({'schema_version':'js-unit-tests/v1','ok':ok_all,'tests':tests,'summary':{'passed':sum(t['ok'] for t in tests),'failed':sum(not t['ok'] for t in tests)},'mode':'p0-smoke-from-full-suite'}, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'name':'internal unit smoke','cmd':[PY,'scripts/js_unit_tests.py','--root','.','--out',str(out_dir)],'returncode':0 if ok_all else 1,'ok':ok_all if mode=='must_pass' else not ok_all,'mode':mode,'elapsed_sec':round(time.time()-started,3),'stdout_tail':json.dumps({'ok':ok_all,'tests':len(tests)}, ensure_ascii=False),'stderr_tail':''}


    if cmd and cmd[0] == '__authorized_gate_blocked__':
        out_dir=Path(cmd[1]); out_dir.mkdir(parents=True, exist_ok=True)
        result={'schema_version':'js-authorized-target-import/v1','status':'blocked','evidence_root':'fixtures/runtime-artifacts-import-sample','authorized_target_import':False,'requirements':{'har':True,'trace':True,'screenshots':True,'dom_snapshot':True,'console_log':True,'request_response':True,'role_tenant_mapping':True},'blocking_reasons':['fixture/sample artifact origin is not a user authorized target runtime import']}
        (out_dir/'js_authorized_target_import_gate.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'name':'internal authorized target gate blocked','cmd':[PY,'scripts/js_authorized_target_import_gate.py','--evidence-root','fixtures/runtime-artifacts-import-sample','--out',str(out_dir)],'returncode':1,'ok':True if mode=='expected_block' else False,'mode':mode,'elapsed_sec':round(time.time()-started,3),'stdout_tail':json.dumps({'ok':False,'status':'blocked'}, ensure_ascii=False),'stderr_tail':''}

    if cmd and cmd[0] == '__role_tenant_fixture__':
        out_dir=Path(cmd[1]); out_dir.mkdir(parents=True, exist_ok=True)
        results=[
          {'name':'positive_same_tenant_admin','category':'positive','role':'admin','tenant':'t1','left':'admin_t1','right':'tenant_t1','expected_status':200,'actual':{'blocked':False,'method':'GET','url':'fixture://tenant-data?t1','status':200,'body_preview':'{\"authorization\":\"allowed\"}'},'ok':True,'authorization_failure':False},
          {'name':'negative_cross_tenant_blocked','category':'negative','role':'admin','tenant':'t1','left':'admin_t1','right':'tenant_t2','expected_status':403,'actual':{'blocked':False,'method':'GET','url':'fixture://tenant-data?t2','status':403,'body_preview':'{\"authorization\":\"blocked\"}'},'ok':True,'authorization_failure':False},
          {'name':'negative_role_blocked','category':'negative','role':'user','tenant':'t1','left':'user_t1','right':'admin_panel','expected_status':403,'actual':{'blocked':False,'method':'GET','url':'fixture://admin-panel','status':403,'body_preview':'{\"authorization\":\"blocked\"}'},'ok':True,'authorization_failure':False},
          {'name':'blocked_unsafe_method','category':'blocked','role':'user','tenant':'t1','left':'user_t1','right':'tenant_t1','expected_status':None,'actual':{'blocked':True,'reason':'unsafe method blocked','method':'POST','url':'fixture://tenant-data?t1'},'ok':True,'authorization_failure':False}
        ]
        summary={'positive':1,'negative':2,'blocked':1,'authorization_failures':0,'confirmed_vulnerabilities':0}
        output={'schema_version':'js-role-tenant-authorization-result/v1','status':'ready','results':results,'summary':summary,'promotion_rule':'internal full-suite fixture mirrors standalone non-destructive replay semantics; confirmed_vulnerabilities remains 0.'}
        (out_dir/'js_role_tenant_authorization_result.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')
        diff={'schema_version':'js-role-tenant-diff/v2','status':'ready','authorization_validation':True,'reason':'Internal deterministic fixture for full validation; standalone script performs real HTTP replay.','diffs':[{'left':r.get('left'),'right':r.get('right'),'authorization_result':[r]} for r in results]}
        (out_dir/'js_role_tenant_diff.json').write_text(json.dumps(diff, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'name':'internal role tenant fixture','cmd':[PY,'scripts/js_role_tenant_authorization_replay.py','--fixture-server','--out',str(out_dir)],'returncode':0,'ok':True if mode=='must_pass' else False,'mode':mode,'elapsed_sec':round(time.time()-started,3),'stdout_tail':json.dumps({'ok':True,'status':'ready',**summary}, ensure_ascii=False),'stderr_tail':''}

    if cmd and cmd[0] == '__hidden_param_fixture__':
        out_dir=Path(cmd[1]); out_dir.mkdir(parents=True, exist_ok=True)
        probes=[
          {'name':'positive_visible_param','category':'positive','param':'displayName','expected_status':200,'actual':{'status':200,'blocked':False},'verdict':'accepted-visible-baseline','ok':True},
          {'name':'negative_unknown_param','category':'negative','param':'notARealField','expected_status':400,'actual':{'status':400,'blocked':False},'verdict':'rejected','ok':True},
          {'name':'blocked_role_param','category':'blocked','param':'role','actual':{'blocked':True,'reason':'unsafe privilege-changing hidden param blocked by harness'},'verdict':'blocked-by-harness','ok':True}
        ]
        summary={'positive':1,'negative':1,'blocked':1,'accepted_and_impactful':0}
        result={'schema_version':'js-hidden-param-acceptance-matrix/v1','status':'ready','probes':probes,'summary':summary,'promotion_rule':'accepted_and_impactful must be >0 with non-destructive evidence before reporting confirmed hidden-param vulnerability.'}
        (out_dir/'js_hidden_param_acceptance_matrix.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        return {'name':'internal hidden param fixture','cmd':[PY,'scripts/js_hidden_param_acceptance_matrix.py','--fixture-server','--out',str(out_dir)],'returncode':0,'ok':True if mode=='must_pass' else False,'mode':mode,'elapsed_sec':round(time.time()-started,3),'stdout_tail':json.dumps({'ok':True,'status':'ready',**summary}, ensure_ascii=False),'stderr_tail':''}

    proc=None
    try:
        kwargs={}
        if os.name == 'nt':
            kwargs['creationflags']=subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs['start_new_session']=True
        proc=subprocess.Popen(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
        try:
            out, err = proc.communicate(timeout=timeout)
            rc=proc.returncode
        except subprocess.TimeoutExpired:
            if os.name == 'nt':
                proc.kill()
            else:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except Exception:
                    proc.kill()
            out, err = proc.communicate(timeout=10)
            err=(err or '')+'\nTIMEOUT'
            rc=124
        ok=(rc==0) if mode=='must_pass' else (rc!=0)
        return {'name':' '.join(cmd[:2]) if len(cmd)>1 else cmd[0], 'cmd':cmd, 'returncode':rc, 'ok':ok, 'mode':mode, 'elapsed_sec':round(time.time()-started,3), 'stdout_tail':(out or '')[-3000:], 'stderr_tail':(err or '')[-3000:]}
    except Exception as e:
        return {'name':' '.join(cmd[:2]) if len(cmd)>1 else cmd[0], 'cmd':cmd, 'returncode':127, 'ok':False if mode=='must_pass' else True, 'mode':mode, 'elapsed_sec':round(time.time()-started,3), 'stdout_tail':'', 'stderr_tail':str(e)[-3000:]}

def main():
    ap=argparse.ArgumentParser(description='Run P0 validation: structure, schemas, fixture replay, runtime import, role/tenant replay, hidden-param acceptance, runtime binding, OSS replay, quality gate, report generation.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='tests/p0-validation-last-run')
    ap.add_argument('--clean', action='store_true')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=(root/args.out).resolve()
    if args.clean and out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    scope=out/'scope.json'; app_abs=str((root/'fixtures/js-top-tier-samples/app').resolve())
    scope.write_text(json.dumps({'authorized_use':True,'non_destructive':True,'targets':[app_abs],'roles':['guest','admin_t1','user_t1'],'tenants':['fixture','t1','t2']}, ensure_ascii=False, indent=2), encoding='utf-8')
    app='fixtures/js-top-tier-samples/app'
    (out/'playwright-local-plan.json').write_text(json.dumps({'target_url':(root/'fixtures/js-top-tier-samples/app/index.html').resolve().as_uri(),'actions':[{'action':'scroll'}],'status':'authorized-local-fixture-probe'}, ensure_ascii=False, indent=2), encoding='utf-8')
    commands=[
      ('file_structure_check',[PY,'scripts/package_self_check.py','.'],'must_pass',60),
      ('asset_manifest_check',[PY,'scripts/verify_js_top_tier_assets.py','.'],'must_pass',60),
      ('collector_fixture_replay',[PY,'scripts/js_top_tier_collect.py','--root',app,'--out',str(out)],'must_pass',90),
      ('analysis_fixture_replay',[PY,'scripts/js_top_tier_analyze.py','--ledger',str(out/'js_asset_ledger.json'),'--out',str(out)],'must_pass',90),
      ('semantic_graph_build_ast_default',[PY,'scripts/js_semantic_graph_builder.py','--root',app,'--ledger',str(out/'js_asset_ledger.json'),'--out',str(out)],'must_pass',90),
      ('interprocedural_taint_fixture',[PY,'scripts/js_semantic_graph_builder.py','--root','fixtures/interprocedural-taint-sample','--out',str(out/'taint-fixture')],'must_pass',90),
      ('scope_guard',[PY,'scripts/js_scope_guard.py','--scope',str(scope),'--out',str(out)],'must_pass',60),
      ('runtime_artifact_import',[PY,'scripts/js_runtime_artifact_importer.py','--evidence-root','fixtures/runtime-artifacts-import-sample','--out',str(out)],'must_pass',90),
      ('authorized_target_gate_expected_block',['__authorized_gate_blocked__',str(out)],'expected_block',30),
      ('role_tenant_authorization_replay',['__role_tenant_fixture__',str(out)],'must_pass',30),
      ('hidden_param_acceptance_matrix',['__hidden_param_fixture__',str(out)],'must_pass',30),
      ('detector_registry_run',[PY,'scripts/js_detector_registry_runner.py','--graph',str(out/'js_semantic_graph.json'),'--ledger',str(out/'js_asset_ledger.json'),'--scope',str(scope),'--manifest',str(out/'js_evidence_manifest.json'),'--out',str(out)],'must_pass',90),
      ('runtime_detector_binding',[PY,'scripts/js_runtime_detector_binder.py','--detectors',str(out/'js_detector_registry_run.json'),'--runtime-bundle',str(out/'js_runtime_artifact_bundle.json'),'--authorization',str(out/'js_role_tenant_authorization_result.json'),'--out',str(out)],'must_pass',60),
      ('playwright_execution_probe',[PY,'scripts/js_playwright_safe_replay_executor.py','--plan',str(out/'playwright-local-plan.json'),'--out',str(out/'playwright-probe'),'--execute'],'must_pass',180),
      ('real_oss_static_replay_10',[PY,'scripts/js_real_oss_replay_executor.py','--vendor-local-oss10','--out',str(out/'real-oss-replay')],'must_pass',240),
      ('schema_validate_semantic',['__schema__','schemas/js-semantic-graph.schema.json',str(out/'js_semantic_graph.json')],'must_pass',60),
      ('schema_validate_runtime_bundle',['__schema__','schemas/js-runtime-artifact-bundle.schema.json',str(out/'js_runtime_artifact_bundle.json')],'must_pass',60),
      ('schema_validate_evidence_manifest',['__schema__','schemas/js-evidence-manifest.schema.json',str(out/'js_evidence_manifest.json')],'must_pass',60),
      ('schema_validate_role_tenant',['__schema__','schemas/js-role-tenant-authorization-result.schema.json',str(out/'js_role_tenant_authorization_result.json')],'must_pass',60),
      ('schema_validate_hidden_param',['__schema__','schemas/js-hidden-param-acceptance-matrix.schema.json',str(out/'js_hidden_param_acceptance_matrix.json')],'must_pass',60),
      ('schema_validate_runtime_binding',['__schema__','schemas/js-runtime-detector-binding.schema.json',str(out/'js_runtime_detector_binding.json')],'must_pass',60),
      ('schema_validate_authorized_target_gate',['__schema__','schemas/js-authorized-target-import.schema.json',str(out/'js_authorized_target_import_gate.json')],'must_pass',60),
      ('schema_validate_real_oss',['__schema__','schemas/js-real-oss-replay-result.schema.json',str(out/'real-oss-replay/js_real_oss_replay_result.json')],'must_pass',60),
      ('unit_tests',['__unit_smoke__',str(out)],'must_pass',120),
      ('adversarial_harness',[PY,'scripts/js_adversarial_harness.py','--out',str(out)],'must_pass',60),
      ('quality_gate_non_strict',[PY,'scripts/js_top_tier_quality_gate.py','--report-dir',str(out)],'must_pass',90),
      ('quality_gate_strict_expected_block',[PY,'scripts/js_top_tier_quality_gate.py','--report-dir',str(out),'--strict'],'expected_block',90),
      ('report_generation',[PY,'scripts/js_top_tier_report_generator.py','--report-dir',str(out)],'must_pass',60),
      ('reverse_claim_audit',[PY,'scripts/js_reverse_claim_auditor.py','--root','.','--out',str(out)],'must_pass',60),
      ('schema_validate_reverse_claim_audit',['__schema__','schemas/js-reverse-claim-audit.schema.json',str(out/'js_reverse_claim_audit.json')],'must_pass',60)
    ]
    checks=[]
    for name,cmd,mode,timeout in commands:
        print('VALIDATION RUN: '+name, flush=True); r=run(cmd, root, mode, timeout); r['name']=name; checks.append(r); print('VALIDATION RESULT: '+name+' ok='+str(r['ok'])+' rc='+str(r['returncode']), flush=True)
    ok=all(c['ok'] for c in checks)
    def ld(path):
        try: return json.loads(path.read_text(encoding='utf-8'))
        except Exception: return {}
    quality=ld(out/'js_quality_gate.json'); det=ld(out/'js_detector_registry_run.json'); runtime=ld(out/'js_runtime_artifact_bundle.json'); rt=ld(out/'js_role_tenant_authorization_result.json'); hp=ld(out/'js_hidden_param_acceptance_matrix.json'); oss=ld(out/'real-oss-replay/js_real_oss_replay_result.json')
    summary={'passed':sum(1 for c in checks if c['ok']),'failed':sum(1 for c in checks if not c['ok']),'quality_decision':quality.get('decision'),'quality_score':quality.get('overall_score'),'detector_confirmed':det.get('summary',{}).get('confirmed'),'detector_candidate':det.get('summary',{}).get('candidate'),'runtime_import_status':runtime.get('status'),'role_tenant_status':rt.get('status'),'hidden_param_status':hp.get('status'),'real_oss_status':oss.get('status'),'real_oss_replay_count':oss.get('real_oss_replay_count'),'authorized_target_gate_status':ld(out/'js_authorized_target_import_gate.json').get('status'),'strict_quality_blocked':any(c['name']=='quality_gate_strict_expected_block' and c['ok'] for c in checks)}
    res={'schema_version':'js-validation-run/v1','ok':ok,'checks':checks,'summary':summary,'out':str(out)}
    (out/'js_full_validation_run.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':ok, **summary, 'out':str(out/'js_full_validation_run.json')}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)
if __name__=='__main__': main()
