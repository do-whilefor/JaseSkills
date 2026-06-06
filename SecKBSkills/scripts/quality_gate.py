#!/usr/bin/env python3
"""SecKB quality gate.
Checks local JSON records. It does not confirm vulnerabilities.
"""
import argparse, json, pathlib, sys

PROMOTED_REQUIRED = [
    "id", "title", "type", "category", "severity", "affected_products",
    "affected_versions", "published_date", "updated_date", "source_urls",
    "source_type", "source_confidence", "summary", "root_cause",
    "attack_preconditions", "impact", "dynamic_validation_safe_method",
    "local_lab_only", "false_positive_conditions", "cannot_report_reasons",
    "evidence_requirements", "patch_or_mitigation", "tags", "last_checked"
]

FORBIDDEN_PROMOTED_SOURCE_TYPES = {"unknown"}
LOW_CONFIDENCE_TYPES = {"community", "unknown"}


def nonempty(v):
    if v is None: return False
    if isinstance(v, str): return bool(v.strip())
    if isinstance(v, (list, dict, tuple, set)): return bool(v)
    return True


def check_record(r):
    problems = []
    status = r.get("review_status")
    if status not in {"promoted", "needs_review", "conflict", "stale", "rejected"}:
        problems.append("invalid_review_status")
    if status != "promoted":
        return problems
    for f in PROMOTED_REQUIRED:
        if not nonempty(r.get(f)):
            problems.append(f"promoted_missing:{f}")
    if int(r.get("source_confidence") or 0) < 75:
        problems.append("promoted_low_source_confidence")
    if r.get("source_type") in FORBIDDEN_PROMOTED_SOURCE_TYPES:
        problems.append("promoted_forbidden_source_type")
    if r.get("source_type") in LOW_CONFIDENCE_TYPES and len(r.get("source_urls") or []) < 2:
        problems.append("promoted_low_confidence_without_cross_validation")
    if r.get("local_lab_only") is not True:
        problems.append("promoted_missing_local_lab_only_true")
    if r.get("source_conflict_fields"):
        problems.append("promoted_has_unresolved_conflict")
    if r.get("example_only") is True:
        problems.append("promoted_example_record")
    return problems


def load_records(path):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    if text.lstrip().startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    args = ap.parse_args()
    records = load_records(args.input)
    failures = []
    for r in records:
        probs = check_record(r)
        if probs:
            failures.append({
                "id": r.get("id"),
                "title": r.get("title"),
                "review_status": r.get("review_status"),
                "problems": probs,
                "suggested_status": "needs_review" if r.get("review_status") == "promoted" else r.get("review_status", "needs_review")
            })
    pathlib.Path(args.output).write_text(json.dumps(failures, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"quality_failures={len(failures)}")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
