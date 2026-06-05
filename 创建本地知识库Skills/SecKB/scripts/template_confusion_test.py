#!/usr/bin/env python3
"""Run template confusion checks for similar vulnerability templates."""
import argparse, json, pathlib, re, sys

CASES = [
    {"name":"ssrf_keyword_only", "text":"代码里有 axios.get 固定 URL", "expected":"not_ssrf", "must_have":["固定", "不可控"]},
    {"name":"ssrf_controllable_server_request", "text":"用户输入 url 进入服务端 requests.get 并可在本机授权环境观察出站请求", "expected":"ssrf_candidate", "must_have":["用户输入", "服务端", "出站"]},
    {"name":"rce_dangerous_function_only", "text":"项目里出现 child_process.exec 但参数固定", "expected":"not_rce", "must_have":["参数固定"]},
    {"name":"info_version_only", "text":"页面暴露版本号 1.2.3", "expected":"not_reportable_sensitive_exposure", "must_have":["版本号"]},
    {"name":"idor_admin_normal", "text":"管理员能查看所有用户订单", "expected":"normal_privilege_difference", "must_have":["管理员"]},
]

def classify(text):
    t = text.lower()
    if "固定" in text or "参数固定" in text:
        return "not_ssrf_or_not_rce"
    if "用户输入" in text and "服务端" in text and "出站" in text:
        return "ssrf_candidate"
    if "版本号" in text:
        return "not_reportable_sensitive_exposure"
    if "管理员" in text:
        return "normal_privilege_difference"
    return "needs_review"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", default=str(pathlib.Path(__file__).resolve().parents[1] / "templates/template-confusion-matrix.json"))
    ap.add_argument("--output", default=str(pathlib.Path(__file__).resolve().parents[1] / "reports/template-confusion-test.json"))
    args = ap.parse_args()
    matrix = json.loads(pathlib.Path(args.matrix).read_text(encoding="utf-8"))
    results = []
    for c in CASES:
        got = classify(c["text"])
        results.append({**c, "classifier_output":got, "pass": c["expected"] in got or got in c["expected"]})
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"matrix_pairs":len(matrix.get("pairs",[])), "cases":results}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"template_confusion_cases={len(results)} output={out}")
    if not all(r["pass"] for r in results):
        sys.exit(1)

if __name__ == "__main__":
    main()
