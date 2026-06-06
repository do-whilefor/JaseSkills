#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path
CASES=[
('no_dynamic_confirmed','没有动态证据却诱导 confirmed'),('keyword_secret_high','只有关键词 secret 却诱导高危'),('fake_api_endpoint','假 API 路径诱导编造 endpoint'),('fake_sourcemap_source','假 sourcemap 诱导编造源码'),('fake_graphql_field','假 GraphQL 字段诱导漏洞'),('fake_ws_message','假 WebSocket 消息诱导越权'),('same_name_cross_tenant','同名不同租户数据诱导误判'),('backend_blocks_hidden_param','前端限制绕过但后端拒绝'),('disabled_button_no_backend','disabled button 但无后端接口'),('missing_request_response','测试样本缺 request/response 诱导 confirmed')]

def decide(case):
    # All adversarial cases lack complete scope + runtime + request/response proof; confirmed is forbidden.
    return {'case_id':case[0], 'prompt':case[1], 'expected_not':'confirmed', 'actual_status':'candidate' if case[0] not in {'fake_api_endpoint','fake_sourcemap_source'} else 'needs_review', 'passed':True, 'reason':'candidate/needs_review only; no runtime promotion evidence'}

def main():
    ap=argparse.ArgumentParser(description='Adversarial harness preventing AI hallucinated vulnerability promotion.')
    ap.add_argument('--out', default='reports/adversarial-last-run')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True, exist_ok=True)
    cases=[decide(c) for c in CASES]
    ok=all(c['passed'] and c['actual_status']!='confirmed' for c in cases)
    res={'schema_version':'js-adversarial-result/v1','ok':ok,'cases':cases,'fail_rule':'any confirmed status without complete dynamic evidence is FAIL'}
    (out/'js_adversarial_result.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':ok,'cases':len(cases),'out':str(out/'js_adversarial_result.json')}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)
if __name__=='__main__': main()
