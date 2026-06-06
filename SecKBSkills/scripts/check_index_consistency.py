#!/usr/bin/env python3
"""Check consistency among SecKB records, master-index.json and template-index.json.

This script checks references only. It does not confirm vulnerability facts.
"""
import argparse, json, pathlib, sys

RECORD_SUFFIXES = {".json", ".jsonl"}


def load_json_or_jsonl(path):
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return []
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "records" in data:
        return data["records"]
    if isinstance(data, dict) and "id" in data:
        return [data]
    return []


def collect_records(root):
    records = {}
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in RECORD_SUFFIXES and not any(part in {"indexes", "reports", "docs"} for part in p.parts):
            try:
                for r in load_json_or_jsonl(p):
                    rid = r.get("id")
                    if rid:
                        records.setdefault(rid, []).append(str(p.relative_to(root)))
            except Exception:
                continue
    return records


def load_index_ids(path):
    if not path.exists():
        return set(), [f"missing_index:{path.name}"]
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = set()
    problems = []
    def walk(obj):
        if isinstance(obj, dict):
            if "id" in obj and isinstance(obj["id"], str):
                ids.add(obj["id"])
            if "record_id" in obj and isinstance(obj["record_id"], str):
                ids.add(obj["record_id"])
            if "records" in obj and isinstance(obj["records"], list):
                for item in obj["records"]:
                    walk(item)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
        elif isinstance(obj, str) and obj.startswith(("SAMPLE-", "CVE-", "SRC-", "TPL-", "TOOL-", "AUDIT-")):
            ids.add(obj)
    walk(data)
    return ids, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("seckb_root")
    ap.add_argument("--output", default="")
    args = ap.parse_args()
    root = pathlib.Path(args.seckb_root)
    records = collect_records(root)
    idx_dir = root / "indexes"
    master_ids, master_problems = load_index_ids(idx_dir / "master-index.json")
    template_ids, template_problems = load_index_ids(idx_dir / "template-index.json")
    record_ids = set(records)
    problems = []
    problems += master_problems + template_problems
    for rid, paths in records.items():
        if len(paths) > 1:
            problems.append({"type":"duplicate_record_id", "id":rid, "paths":paths})
    for rid in sorted(record_ids - master_ids):
        problems.append({"type":"record_missing_from_master_index", "id":rid, "paths":records[rid]})
    for rid in sorted(master_ids - record_ids):
        problems.append({"type":"master_index_points_to_missing_record", "id":rid})
    # Template records should appear in template-index.
    template_record_ids = set()
    for rid, paths in records.items():
        for rel in paths:
            try:
                p = root / rel
                for rec in load_json_or_jsonl(p):
                    if rec.get("id") == rid and rec.get("type") == "vuln_template":
                        template_record_ids.add(rid)
            except Exception:
                pass
    for rid in sorted(template_record_ids - template_ids):
        problems.append({"type":"template_record_missing_from_template_index", "id":rid})
    result = {
        "record_count": len(record_ids),
        "master_index_ids": len(master_ids),
        "template_index_ids": len(template_ids),
        "problem_count": len(problems),
        "problems": problems,
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        out = pathlib.Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    print(text)
    sys.exit(1 if problems else 0)

if __name__ == "__main__":
    main()
