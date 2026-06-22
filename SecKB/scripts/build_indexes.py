#!/usr/bin/env python3
import argparse, json, pathlib, collections

INDEX_FILES = {
    "source-index.json": lambda r: r.get("source_type", "unknown"),
    "cve-index.json": lambda r: r.get("id", "") if r.get("type") in {"cve", "advisory"} else None,
    "src-rules-index.json": lambda r: r.get("id", "") if r.get("type") == "src_rule" else None,
    "tool-release-index.json": lambda r: r.get("id", "") if r.get("type") == "tool_release" else None,
    "template-index.json": lambda r: r.get("id", "") if r.get("type") in {"vuln_template", "code_audit_pattern", "report_template"} else None,
}


def compact(r):
    return {
        "id": r.get("id"),
        "title": r.get("title"),
        "type": r.get("type"),
        "category": r.get("category"),
        "review_status": r.get("review_status"),
        "source_confidence": r.get("source_confidence"),
        "tags": r.get("tags", []),
        "last_checked": r.get("last_checked"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("index_dir")
    args = ap.parse_args()
    records = json.loads(pathlib.Path(args.records).read_text(encoding="utf-8"))
    outdir = pathlib.Path(args.index_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    master = {
        "routing_policy": "index_first_then_detail",
        "counts": dict(collections.Counter(r.get("review_status", "unknown") for r in records)),
        "by_type": dict(collections.Counter(r.get("type", "unknown") for r in records)),
        "records": [compact(r) for r in records]
    }
    (outdir / "master-index.json").write_text(json.dumps(master, ensure_ascii=False, indent=2), encoding="utf-8")

    for name, selector in INDEX_FILES.items():
        items = []
        for r in records:
            if selector(r):
                items.append(compact(r))
        (outdir / name).write_text(json.dumps({"items": items}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"built indexes in {outdir}")

if __name__ == "__main__":
    main()
