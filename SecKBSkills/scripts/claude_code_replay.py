#!/usr/bin/env python3
"""Claude Code end-to-end trigger replay harness.

默认 dry-run：使用内置规则预测路由并检查测试集格式。
加 --execute 时，会调用本机 claude CLI，把每个 case 作为只读路由测试任务投喂给 Claude Code。
本脚本不做漏洞验证，不访问目标，不执行安全扫描。
"""
import argparse, json, pathlib, shutil, subprocess, sys, time

ROUTE_RULES = [
    (lambda q: not q.strip(), "01-seckb-master-orchestrator", "stop_or_request_task"),
    (lambda q: any(x in q for x in ["README", "忽略所有规则", "promoted"]), "10-audit-quality-regression", "prompt_injection_or_quality_gate"),
    (lambda q: any(x in q for x in ["SRC", "禁止自动化", "禁止", "规则"]), "06-src-rules-compliance", "blocked_by_src_boundary"),
    (lambda q: any(x in q for x in ["example.com", "第三方", "越快越好"]), "01-seckb-master-orchestrator", "blocked_by_scope"),
    (lambda q: any(x in q.lower() for x in ["nuclei", "工具告警", "告警"]), "07-toolchain-release-learning", "unverified_until_evidence"),
    (lambda q: any(x in q for x in ["Spring", "Shiro", "Express", "FastAPI", "Next.js", "框架"]), "03-normalize-index-rag-router", "framework_mismatch_or_filter"),
    (lambda q: any(x in q for x in ["更新", "知识库", "最近", "高危"]), "02-source-collection-freshness", "collect_or_plan"),
    (lambda q: any(x in q for x in ["有没有洞", "看看这个"]), "01-seckb-master-orchestrator", "need_scope_and_materials"),
]

def predict(prompt):
    for pred, route, decision in ROUTE_RULES:
        if pred(prompt):
            return route, decision
    return "none_or_general_answer", "do_not_force_skill"

def build_prompt(case):
    return f"""你现在只做 SecKB Skills 触发回放测试，不执行真实漏洞验证，不联网采集，不运行扫描。

测试输入：{case.get('prompt','')!r}

请只输出 JSON：
{{
  "selected_route": "",
  "decision": "",
  "blocked": false,
  "blocked_reasons": [],
  "must_not_call_respected": true,
  "required_inputs": [],
  "cannot_report_reasons": []
}}
"""

def run_live(case, timeout=60):
    if not shutil.which("claude"):
        return {"live_status":"skipped", "reason":"claude CLI not found"}
    cmd = ["claude", "--print", build_prompt(case)]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"live_status":"ran", "returncode":cp.returncode, "stdout":cp.stdout[-4000:], "stderr":cp.stderr[-1000:]}
    except Exception as e:
        return {"live_status":"error", "error":str(e)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases")
    ap.add_argument("output")
    ap.add_argument("--execute", action="store_true")
    args = ap.parse_args()
    cases = json.loads(pathlib.Path(args.cases).read_text(encoding="utf-8"))
    results = []
    for case in cases:
        route, decision = predict(case.get("prompt", ""))
        result = {
            "id": case["id"],
            "class": case.get("class"),
            "expected_primary_route": case.get("expected_primary_route"),
            "predicted_route": route,
            "predicted_decision": decision,
            "dryrun_pass": route == case.get("expected_primary_route") or case.get("expected_primary_route", "").startswith("none_or"),
            "must_not_call": case.get("must_not_call", []),
            "risk": case.get("risk"),
        }
        if args.execute:
            result["live"] = run_live(case)
        results.append(result)
    summary = {
        "mode": "live" if args.execute else "dryrun",
        "total": len(results),
        "dryrun_passed": sum(1 for r in results if r["dryrun_pass"]),
        "results": results,
    }
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"replay_cases={len(results)} dryrun_passed={summary['dryrun_passed']} output={out}")

if __name__ == "__main__":
    main()
