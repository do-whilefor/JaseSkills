#!/usr/bin/env python3
import argparse, json, pathlib, sys

REQUIRED = [
    "README.md",
    "CAPABILITY_INDEX.md",
    "01-seckb-master-orchestrator/SKILL.md",
    "10-audit-quality-regression/SKILL.md",
    "docs/quality-gate-policy.md",
    "docs/anti-hallucination-policy.md",
    "docs/v3-enhancement-report.md",
    "templates/record.schema.json",
    "templates/evidence-manifest.schema.json",
    "templates/template-confusion-matrix.json",
    "scripts/quality_gate.py",
    "scripts/claude_code_replay.py",
    "scripts/check_index_consistency.py",
    "scripts/dashboard_build.py",
    "scripts/template_confusion_test.py",
    "tests/claude-code-replay/replay-cases.json",
    "testdata/quality-gate/records_100.json",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("output")
    args = ap.parse_args()
    root = pathlib.Path(args.root)
    missing = [p for p in REQUIRED if not (root / p).exists()]
    result = {"required_count":len(REQUIRED), "missing":missing, "passed":not missing}
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1 if missing else 0)

if __name__ == "__main__":
    main()
