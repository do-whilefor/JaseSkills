#!/usr/bin/env python3
"""Build SecKB dashboard as Markdown or static HTML.
Shows source confidence, freshness, conflicts and human-confirmation queue.
"""
import argparse, json, pathlib, collections, html, statistics
from datetime import date, datetime

def load_records(path):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    if text.lstrip().startswith("["):
        return json.loads(text)
    return [json.loads(line) for line in text.splitlines() if line.strip()]

def freshness_bucket(r, today=date(2026,6,4)):
    val = r.get("last_checked") or r.get("updated_date") or r.get("published_date")
    try:
        d = datetime.fromisoformat(val[:10]).date()
        days = (today - d).days
    except Exception:
        return "unknown"
    if days <= 30: return "fresh_0_30d"
    if days <= 90: return "aging_31_90d"
    return "stale_90d_plus"

def esc(x): return html.escape(str(x if x is not None else ""))

def build_markdown(records):
    status = collections.Counter(r.get("review_status", "unknown") for r in records)
    types = collections.Counter(r.get("type", "unknown") for r in records)
    freshness = collections.Counter(freshness_bucket(r) for r in records)
    conflicts = [r for r in records if r.get("review_status") == "conflict" or r.get("source_conflict_fields")]
    queue = sorted([r for r in records if r.get("review_status") in {"needs_review","conflict","stale"}], key=lambda x: (x.get("review_status") != "conflict", -(int(x.get("source_confidence") or 0))))[:50]
    lines = ["# SecKB Dashboard", "", "## 状态统计", ""]
    for k, v in status.items(): lines.append(f"- {k}: {v}")
    lines += ["", "## 类型统计", ""]
    for k, v in types.items(): lines.append(f"- {k}: {v}")
    lines += ["", "## Freshness", ""]
    for k, v in freshness.items(): lines.append(f"- {k}: {v}")
    lines += ["", "## 来源可信度", ""]
    confs = [int(r.get("source_confidence") or 0) for r in records]
    if confs:
        lines.append(f"- min/avg/max: {min(confs)} / {statistics.mean(confs):.1f} / {max(confs)}")
    lines += ["", "## 冲突条目", "", "| ID | 标题 | 冲突字段 | 来源可信度 |", "|---|---|---|---:|"]
    for r in conflicts[:50]:
        lines.append(f"| {r.get('id','')} | {r.get('title','')} | {', '.join(r.get('source_conflict_fields', []))} | {r.get('source_confidence',0)} |")
    lines += ["", "## 人工确认优先队列", "", "| ID | 标题 | 类型 | 状态 | 来源可信度 | freshness |", "|---|---|---|---|---:|---|"]
    for r in queue:
        lines.append(f"| {r.get('id','')} | {r.get('title','')} | {r.get('type','')} | {r.get('review_status','')} | {r.get('source_confidence',0)} | {freshness_bucket(r)} |")
    return "\n".join(lines) + "\n"

def bar(label, value, total):
    pct = 0 if total == 0 else int(value * 100 / total)
    return f'<div class="bar-row"><span>{esc(label)}</span><div class="bar"><i style="width:{pct}%"></i></div><b>{value}</b></div>'

def build_html(records):
    status = collections.Counter(r.get("review_status", "unknown") for r in records)
    freshness = collections.Counter(freshness_bucket(r) for r in records)
    conflicts = [r for r in records if r.get("review_status") == "conflict" or r.get("source_conflict_fields")]
    queue = sorted([r for r in records if r.get("review_status") in {"needs_review","conflict","stale"}], key=lambda x: (x.get("review_status") != "conflict", -(int(x.get("source_confidence") or 0))))[:100]
    total = len(records)
    confs = [int(r.get("source_confidence") or 0) for r in records]
    avg_conf = statistics.mean(confs) if confs else 0
    cards = f"""
    <section class="cards">
      <div class="card"><h3>Total records</h3><p>{total}</p></div>
      <div class="card"><h3>Average confidence</h3><p>{avg_conf:.1f}</p></div>
      <div class="card"><h3>Conflicts</h3><p>{len(conflicts)}</p></div>
      <div class="card"><h3>Human queue</h3><p>{len(queue)}</p></div>
    </section>
    """
    status_html = "".join(bar(k, v, total) for k, v in status.items())
    fresh_html = "".join(bar(k, v, total) for k, v in freshness.items())
    conflict_rows = "".join(f"<tr><td>{esc(r.get('id'))}</td><td>{esc(r.get('title'))}</td><td>{esc(', '.join(r.get('source_conflict_fields', [])))}</td><td>{esc(r.get('source_confidence'))}</td></tr>" for r in conflicts[:50])
    queue_rows = "".join(f"<tr><td>{esc(r.get('id'))}</td><td>{esc(r.get('title'))}</td><td>{esc(r.get('type'))}</td><td>{esc(r.get('review_status'))}</td><td>{esc(r.get('source_confidence'))}</td><td>{esc(freshness_bucket(r))}</td></tr>" for r in queue[:100])
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>SecKB Dashboard</title>
<style>
body{{font-family:system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:28px;background:#f7f7f8;color:#171717}}
h1{{margin-bottom:4px}} .sub{{color:#666;margin-top:0}}
.cards{{display:grid;grid-template-columns:repeat(4,minmax(160px,1fr));gap:12px;margin:20px 0}}
.card{{background:white;border:1px solid #e6e6e6;border-radius:12px;padding:16px}} .card h3{{font-size:14px;color:#666;margin:0 0 8px}} .card p{{font-size:28px;margin:0}}
.panel{{background:white;border:1px solid #e6e6e6;border-radius:12px;padding:16px;margin:14px 0}}
.bar-row{{display:grid;grid-template-columns:180px 1fr 60px;align-items:center;gap:10px;margin:8px 0}} .bar{{height:10px;background:#eee;border-radius:6px;overflow:hidden}} .bar i{{display:block;height:100%;background:#555}}
table{{width:100%;border-collapse:collapse;background:white}} th,td{{border-bottom:1px solid #eee;text-align:left;padding:8px;vertical-align:top}} th{{color:#555;font-size:13px}}
</style></head><body>
<h1>SecKB Dashboard</h1><p class="sub">Static local dashboard. It summarizes records only and does not confirm vulnerabilities.</p>
{cards}
<section class="panel"><h2>Review status</h2>{status_html}</section>
<section class="panel"><h2>Freshness</h2>{fresh_html}</section>
<section class="panel"><h2>Source conflicts</h2><table><thead><tr><th>ID</th><th>Title</th><th>Conflict fields</th><th>Confidence</th></tr></thead><tbody>{conflict_rows}</tbody></table></section>
<section class="panel"><h2>Human confirmation queue</h2><table><thead><tr><th>ID</th><th>Title</th><th>Type</th><th>Status</th><th>Confidence</th><th>Freshness</th></tr></thead><tbody>{queue_rows}</tbody></table></section>
</body></html>"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("records")
    ap.add_argument("output")
    ap.add_argument("--format", choices=["markdown","html"], default="markdown")
    args = ap.parse_args()
    records = load_records(args.records)
    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    content = build_html(records) if args.format == "html" else build_markdown(records)
    output.write_text(content, encoding="utf-8")
    print(f"dashboard={output} format={args.format} records={len(records)}")

if __name__ == "__main__":
    main()
