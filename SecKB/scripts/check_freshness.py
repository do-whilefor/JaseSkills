#!/usr/bin/env python3
import argparse, json, pathlib, datetime


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        try:
            return datetime.datetime.strptime(s[:10], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
        except Exception:
            return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()
    now = datetime.datetime.now(datetime.timezone.utc)
    records = json.loads(pathlib.Path(args.input).read_text(encoding="utf-8"))
    audit = []
    for r in records:
        latest = parse_date(r.get("updated_date")) or parse_date(r.get("published_date"))
        last_checked = parse_date(r.get("last_checked"))
        is_recent = bool(latest and (now - latest).days <= args.days)
        stale = bool(last_checked and (now - last_checked).days > args.days)
        suggested = r.get("review_status", "needs_review")
        if stale:
            suggested = "stale"
        audit.append({
            "id": r.get("id"),
            "title": r.get("title"),
            "published_date": r.get("published_date"),
            "updated_date": r.get("updated_date"),
            "last_checked": r.get("last_checked"),
            "is_recent": is_recent,
            "stale": stale,
            "suggested_status": suggested
        })
    pathlib.Path(args.output).write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"freshness_audited={len(audit)}")

if __name__ == "__main__":
    main()
