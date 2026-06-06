#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SHARED=ROOT/'_shared'
errors=[]
def check(c,msg):
    if not c: errors.append(msg)
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def run_py(path,*args):
    cp=subprocess.run([sys.executable,str(path),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=90,env={'PYTHONDONTWRITEBYTECODE':'1',**os.environ})
    try: obj=json.loads(cp.stdout)
    except Exception: obj={'parse_error':cp.stdout[:500],'stderr':cp.stderr[:500],'returncode':cp.returncode}
    return cp.returncode,obj

def main():
    check((SHARED/'evidence/EVIDENCE_MANIFEST_SCHEMA.v4.3.json').exists(),'missing v4.3 schema')
    rc,parser=run_py(ROOT/'skills/03-code-knowledge-graph/scripts/parser_backends/parser_runtime_manager.py')
    check(parser.get('schema_version')=='parser_runtime_readiness_v4.3','parser runtime manager did not emit v4.3')
    for row in parser.get('languages',[]):
        if row.get('language') in {'java','php','go','rust','ruby'} and not row.get('runtime_ready'):
            check(row.get('promotion_status')=='blocked_until_runtime_ready', f"{row.get('language')} must block promotion when not ready")
    rc,pw=run_py(ROOT/'skills/06-dynamic-browser-burp-mcp/scripts/playwright_runtime_manager.py')
    check(pw.get('schema_version')=='playwright_runtime_readiness_v4.3','playwright runtime manager missing')
    oss=load(SHARED/'tests/oss_replay/oss_replay_index.json')
    check(oss.get('adapter_count',0)>=30,'OSS replay index must contain 30+ adapters')
    rc,ossres=run_py(SHARED/'tests/oss_replay/oss_replay_runner.py')
    check(ossres.get('adapter_count',0)>=30,'OSS replay runner did not load adapters')
    rc,hr=run_py(SHARED/'tests/high_risk_replay/high_risk_replay_runner.py')
    check(hr.get('passed') is True and hr.get('case_count')==28,'high risk replay runner must pass 28 cases')
    js_script=ROOT/'skills/05-js-audit-runtime/scripts/js_deep_semantic_graph.py'
    check(js_script.exists(),'missing JS deep semantic graph')
    sample=SHARED/'tests/e2e_samples/01-express-next'
    rc,jsg=run_py(js_script,str(sample))
    check(jsg.get('schema_version')=='js_deep_semantic_graph_v4.3','JS deep graph did not emit v4.3')
    check('sourcemap_original_spans' in jsg and 'wrapper_interceptor_dataflow' in jsg,'JS deep graph missing required fields')
    check((ROOT/'skills/07-vulnerability-hunting-engine/SOURCE_SINK_DATAFLOW_DETECTOR_SPEC.v4.3.md').exists(),'missing source-sink detector spec')
    check((SHARED/'dashboard/runtime_chain_dashboard_generator.py').exists(),'missing runtime chain dashboard generator')
    taint=load(SHARED/'quality/TAINT_SOURCES.v4.3.json')
    check('sourcemap_sourcesContent' in taint.get('untrusted_sources',[]),'taint sources missing sourcemap')
    res={'schema_version':'v4_3_completion_selftest','passed':not errors,'errors':errors,'parser_runtime_ready_count':parser.get('runtime_ready_count'),'oss_adapter_count':oss.get('adapter_count'),'playwright_browser_runtime_ready':pw.get('browser_runtime_ready')}
    print(json.dumps(res,ensure_ascii=False,indent=2)); return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
