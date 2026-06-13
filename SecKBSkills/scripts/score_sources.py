#!/usr/bin/env python3
import argparse, json, pathlib

SCORES = {
    "official": 95,
    "vendor": 90,
    "platform": 75,
    "research": 60,
    "community": 35,
    "unknown": 10,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    args = ap.parse_args()
    records = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    for r in records:
        st = r.get("source_type", "unknown")
        r["source_confidence"] = max(int(r.get("source_confidence") or 0), SCORES.get(st, 10))
        if st in {"community", "unknown"} and r.get("review_status") == "promoted":
            r["review_status"] = "needs_review"
        if not r.get("source_urls") and r.get("review_status") == "promoted":
            r["review_status"] = "needs_review"
    pathlib.Path(args.output).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"scored={len(records)}")

if __name__ == "__main__":
    main()
