#!/usr/bin/env python3
import argparse, json, pathlib, datetime

REQUIRED_DEFAULTS = {
    "id": "",
    "title": "",
    "type": "advisory",
    "category": "",
    "severity": "",
    "cwe": [],
    "owasp": [],
    "affected_products": [],
    "affected_versions": [],
    "fixed_versions": [],
    "published_date": "",
    "updated_date": "",
    "source_urls": [],
    "source_type": "unknown",
    "source_confidence": 0,
    "summary": "",
    "root_cause": "",
    "attack_preconditions": [],
    "impact": "",
    "dynamic_validation_safe_method": "Local lab or explicitly authorized environment only.",
    "local_lab_only": True,
    "false_positive_conditions": [],
    "cannot_report_reasons": [],
    "evidence_requirements": [],
    "patch_or_mitigation": "",
    "related_records": [],
    "tags": [],
    "last_checked": "",
    "review_status": "needs_review",
    "freshness_scope": "unknown"
}

VALID_STATUS = {"promoted", "needs_review", "conflict", "stale", "rejected"}


def load_records(path):
    p = pathlib.Path(path)
    if p.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    data = json.loads(p.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def normalize(rec):
    out = dict(REQUIRED_DEFAULTS)
    out.update(rec)
    if not out["last_checked"]:
        out["last_checked"] = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    if out["review_status"] not in VALID_STATUS:
        out["review_status"] = "needs_review"
    critical = ["id", "title", "source_urls", "summary"]
    if any(not out.get(k) for k in critical):
        out["review_status"] = "needs_review"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    args = ap.parse_args()
    records = [normalize(r) for r in load_records(args.input)]
    pathlib.Path(args.output).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"normalized={len(records)} output={args.output}")

if __name__ == "__main__":
    main()
