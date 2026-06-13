#!/usr/bin/env python3
import argparse, json, pathlib, hashlib


def key(rec):
    if rec.get("id"):
        return "id:" + rec["id"].lower()
    urls = rec.get("source_urls") or []
    if urls:
        return "url:" + sorted(urls)[0].lower()
    raw = (rec.get("title", "") + "|" + rec.get("category", "")).lower()
    return "hash:" + hashlib.sha256(raw.encode()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    args = ap.parse_args()
    records = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    seen = {}
    conflicts = []
    for r in records:
        k = key(r)
        if k in seen:
            existing = seen[k]
            merged = dict(existing)
            for field in ["source_urls", "related_records", "tags"]:
                merged[field] = sorted(set((existing.get(field) or []) + (r.get(field) or [])))
            if existing.get("affected_versions") != r.get("affected_versions"):
                merged["review_status"] = "conflict"
                conflicts.append({"key": k, "field": "affected_versions", "a": existing.get("affected_versions"), "b": r.get("affected_versions")})
            seen[k] = merged
        else:
            seen[k] = r
    out = list(seen.values())
    pathlib.Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    conflict_path = pathlib.Path(args.output).with_suffix(".conflicts.json")
    conflict_path.write_text(json.dumps(conflicts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"deduped={len(out)} conflicts={len(conflicts)}")

if __name__ == "__main__":
    main()
