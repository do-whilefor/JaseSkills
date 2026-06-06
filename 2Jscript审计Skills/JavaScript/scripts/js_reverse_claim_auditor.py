#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, hashlib, os, re, subprocess, sys
from pathlib import Path
from typing import Any

CLAIMS = [
  {
    "claim":"保留原有 knowledge 知识库文件",
    "paths":["knowledge"],
    "class_if_present":"A",
    "status_if_present":"ready",
    "verdict":"文件级保留可以证明；内容完整性需用原包哈希对比证明。"
  },
  {
    "claim":"保留原有漏洞/报告模板",
    "paths":["templates"],
    "class_if_present":"A",
    "status_if_present":"ready",
    "verdict":"文件级保留可以证明；新增模板不替代原模板。"
  },
  {
    "claim":"skills/ 下 19 个工程化子模块存在 README 和 SKILL",
    "paths":["skills/js-asset-collector/SKILL.md","skills/js-ast-analyzer/SKILL.md","skills/js-api-extractor/SKILL.md","skills/js-sourcemap-analyzer/SKILL.md","skills/js-route-graph/SKILL.md","skills/js-authz-detector/SKILL.md","skills/js-graphql-detector/SKILL.md","skills/js-websocket-detector/SKILL.md","skills/js-postmessage-detector/SKILL.md","skills/js-domxss-detector/SKILL.md","skills/js-secret-detector/SKILL.md","skills/js-business-logic-detector/SKILL.md","skills/dynamic-replay/SKILL.md","skills/evidence-manifest/SKILL.md","skills/quality-gate/SKILL.md","skills/report-templates/SKILL.md","skills/test-fixtures/SKILL.md","skills/adversarial-tests/SKILL.md","skills/docs/SKILL.md"],
    "class_if_present":"A",
    "status_if_present":"ready",
    "verdict":"结构存在属实；不等于每个模块已达到世界顶级执行力。"
  },
  {
    "claim":"JS collector 有真实代码、输入输出和 ledger",
    "paths":["scripts/js_top_tier_collect.py","schemas/js-top-tier-ledger.schema.json","fixtures/js-top-tier-samples/app/index.html"],
    "class_if_present":"A",
    "status_if_present":"ready",
    "cmd":"node scripts/js_cross_platform_runner.mjs fixture:test",
    "verdict":"静态收集和 ledger 产出可运行。动态登录态、角色差异、浏览器缓存覆盖不能由此证明。"
  },
  {
    "claim":"AST/语义分析已实现为真实 AST + dataflow + CFG",
    "paths":["scripts/js_semantic_graph_builder.py","scripts/backends/js/babel_extract.mjs","scripts/backends/js/typescript_extract.mjs","schemas/js-semantic-graph.schema.json"],
    "class_if_present":"B",
    "status_if_present":"partial",
    "cmd":"node scripts/js_cross_platform_runner.mjs semantic:sample",
    "verdict":"存在可运行语义图和可选 Babel/TypeScript backend，但主流程仍含 regex/proximity 逻辑；不得声称完整 CFG/DFG/taint-flow ready。"
  },
  {
    "claim":"API 与隐藏参数发现可运行",
    "paths":["scripts/js_api_parameter_model.py","scripts/js_backend_param_diff.py","schemas/js-api-parameter-model.schema.json","schemas/js-backend-param-diff.schema.json"],
    "class_if_present":"B",
    "status_if_present":"partial",
    "verdict":"前端参数与差异建模可运行；后端 acceptance 需要 request/response 证据，未满足时必须 blocked。"
  },
  {
    "claim":"40 类 detector 全部 ready",
    "paths":["data/js_detector_registry_v2.json","scripts/js_detector_registry_runner.py","schemas/js-detector-registry.schema.json","schemas/js-detector-finding.schema.json"],
    "class_if_present":"B",
    "status_if_present":"partial",
    "cmd":"node scripts/js_cross_platform_runner.mjs detectors:sample",
    "verdict":"registry 和 runner 存在；多数 detector 只能输出 candidate/needs_review，未具备完整动态 promotion。"
  },
  {
    "claim":"Playwright/HAR/trace/screenshot 动态验证闭环已完成",
    "paths":["scripts/js_playwright_safe_replay_executor.py","scripts/js_runtime_evidence_manifest.py","schemas/js-evidence-manifest.schema.json"],
    "class_if_present":"B",
    "status_if_present":"needs_review",
    "verdict":"存在计划生成、HAR 导入和 evidence manifest builder；缺真实 Playwright trace、screenshot、DOM snapshot、多角色请求响应时不得 confirmed。"
  },
  {
    "claim":"多角色、多租户验证已完成",
    "paths":["scripts/js_role_tenant_diff.py","schemas/js-runtime-evidence.schema.json"],
    "class_if_present":"B",
    "status_if_present":"needs_review",
    "verdict":"存在差异脚本；样例没有真实跨角色/跨租户授权结果矩阵，不能声称完成。"
  },
  {
    "claim":"后端接受隐藏参数验证已完成",
    "paths":["scripts/js_backend_acceptance_probe.py","scripts/js_backend_param_diff.py","schemas/js-backend-acceptance-evidence.schema.json"],
    "class_if_present":"B",
    "status_if_present":"needs_review",
    "verdict":"存在非破坏性 probe 脚本和 schema；没有具体后端 positive/negative/blocked 请求响应时只能是 blocked/needs_review。"
  },
  {
    "claim":"quality gate 会失败时阻断",
    "paths":["scripts/js_top_tier_quality_gate.py"],
    "class_if_present":"A",
    "status_if_present":"ready",
    "cmd":"node scripts/js_cross_platform_runner.mjs quality:strict --report-dir tests/reverse-audit-last-run",
    "verdict":"修复后 strict 模式在 not-top-tier 或 blocking 条件存在时返回非零退出码；默认模式只生成报告。"
  },
  {
    "claim":"adversarial harness 防止 AI 编造 confirmed",
    "paths":["scripts/js_adversarial_harness.py","fixtures/adversarial-js-hallucination/cases.json","schemas/js-adversarial-result.schema.json"],
    "class_if_present":"A",
    "status_if_present":"ready",
    "cmd":"node scripts/js_cross_platform_runner.mjs adversarial:test --out tests/reverse-audit-last-run",
    "verdict":"10 个固定诱导样例会强制 candidate/needs_review；它不是完整 LLM 红队评测。"
  },
  {
    "claim":"报告生成可运行",
    "paths":["scripts/js_top_tier_report_generator.py","templates/js-top-tier-report.md"],
    "class_if_present":"A",
    "status_if_present":"ready",
    "cmd":"node scripts/js_cross_platform_runner.mjs report:generate --report-dir tests/reverse-audit-last-run",
    "verdict":"Markdown 报告可生成；报告不得把缺动态证据的项写成 confirmed。"
  },
  {
    "claim":"世界顶级 JS 审计 Skills 已完成",
    "paths":["docs/RUNBOOK.md"],
    "class_if_present":"C",
    "status_if_present":"withdrawn",
    "verdict":"撤回。当前包是证据优先的工程化骨架与候选分析链，距离世界顶级仍缺真实动态、多角色、多租户、后端 acceptance 与完整 CFG/DFG。"
  }
]

def exists(root:Path, rel:str)->bool:
    return (root/rel).exists()

def sha(p:Path)->str:
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def path_evidence(root:Path, paths:list[str])->list[dict[str,Any]]:
    out=[]
    for rel in paths:
        p=root/rel
        item={"path":rel,"exists":p.exists()}
        if p.is_file():
            item.update({"size":p.stat().st_size,"sha256":sha(p)})
        elif p.is_dir():
            files=[x for x in p.rglob('*') if x.is_file()]
            item.update({"file_count":len(files)})
        out.append(item)
    return out

def classify(root:Path)->list[dict[str,Any]]:
    rows=[]
    for c in CLAIMS:
        ev=path_evidence(root, c.get('paths',[]))
        all_present=all(x.get('exists') for x in ev)
        cls=c['class_if_present'] if all_present else 'C'
        status=c['status_if_present'] if all_present else 'blocked'
        verdict=c['verdict'] if all_present else '缺真实文件，原声明撤回。'
        rows.append({"claim":c['claim'],"class":cls,"status":status,"evidence":ev,"verdict":verdict,"required_command":c.get('cmd','')})
    return rows

def main():
    ap=argparse.ArgumentParser(description='Reverse-audit previous capability claims and downgrade unsupported claims.')
    ap.add_argument('--root', default='.')
    ap.add_argument('--out', default='tests/reverse-audit-last-run')
    args=ap.parse_args(); root=Path(args.root).resolve(); out=(root/args.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    rows=classify(root)
    withdrawals=[r for r in rows if r['class']=='C']
    blocking_fixes=[
      {"fix":"quality gate strict mode returns non-zero on not-top-tier", "file":"scripts/js_top_tier_quality_gate.py", "command":"node scripts/js_cross_platform_runner.mjs quality:strict --report-dir tests/reverse-audit-last-run"},
      {"fix":"detector runner blocks static-only promotion", "file":"scripts/js_detector_registry_runner.py", "command":"node scripts/js_cross_platform_runner.mjs detectors:sample"},
      {"fix":"reverse claim audit emits A/B/C downgrade evidence", "file":"scripts/js_reverse_claim_auditor.py", "command":"node scripts/js_cross_platform_runner.mjs reverse:audit"}
    ]
    summary={k:sum(1 for r in rows if r['class']==k) for k in ['A','B','C']}
    res={"schema_version":"js-reverse-claim-audit/v1","ok":True,"summary":summary,"classifications":rows,"withdrawals":withdrawals,"blocking_fixes":blocking_fixes}
    (out/'js_reverse_claim_audit.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    md=['# Ultimate Reverse Judgement','',f"A ready: {summary['A']}",f"B partial/needs_review: {summary['B']}",f"C withdrawn: {summary['C']}",'']
    for r in rows:
        md += [f"## [{r['class']}] {r['claim']}", f"Status: `{r['status']}`", f"Verdict: {r['verdict']}"]
        if r.get('required_command'): md.append(f"Command: `{r['required_command']}`")
        md.append('Evidence:')
        for e in r['evidence']:
            md.append(f"- `{e['path']}` exists={e['exists']}" + (f" size={e.get('size')} sha256={e.get('sha256','')[:12]}" if 'size' in e else f" files={e.get('file_count')}" if 'file_count' in e else ''))
        md.append('')
    (out/'js_reverse_claim_audit.md').write_text('\n'.join(md), encoding='utf-8')
    print(json.dumps({"ok":True,"out":str(out/'js_reverse_claim_audit.json'),"summary":summary}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()
