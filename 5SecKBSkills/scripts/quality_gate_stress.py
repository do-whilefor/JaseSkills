#!/usr/bin/env python3
"""Run SecKB quality gate against the bundled 100-record synthetic sample set."""
import argparse, json, pathlib, subprocess, sys

def main():
    root = pathlib.Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", default=str(root / "testdata/quality-gate/records_100.json"))
    ap.add_argument("--output", default=str(root / "reports/quality-gate-stress.json"))
    args = ap.parse_args()
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    qg = root / "scripts/quality_gate.py"
    cp = subprocess.run([sys.executable, str(qg), args.records, str(out)], text=True, capture_output=True)
    records = json.loads(pathlib.Path(args.records).read_text(encoding="utf-8"))
    failures = json.loads(out.read_text(encoding="utf-8")) if out.exists() else []
    summary = {
        "records": len(records),
        "status_counts": {s: sum(1 for r in records if r.get("review_status") == s) for s in ["promoted","needs_review","conflict","stale","rejected"]},
        "quality_gate_returncode": cp.returncode,
        "quality_gate_stdout": cp.stdout.strip(),
        "quality_gate_stderr": cp.stderr.strip(),
        "failure_count": len(failures),
        "failures_path": str(out),
        "expected": "promoted samples pass; non-promoted samples may keep non-promoted status without forcing failure unless invalid status exists"
    }
    summary_path = out.with_name("quality-gate-stress-summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
