#!/usr/bin/env python3
"""Normalize information-collection candidates into a common evidence ledger.

This script merges local static candidates, JS candidates, config/dependency inventory
and optional runtime summaries. It does not confirm vulnerabilities. It maps fields
needed by severe-vulnerability detectors and marks missing dynamic/auth/tenant data.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "info-surface"
TEMPLATE = "templates/finding-detail.md"

VULN_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("IDOR/BOLA", re.compile(r"\b(userId|user_id|accountId|account_id|objectId|projectId|documentId|orderId|invoiceId|/users?/|/orders?/|/projects?/|/documents?)\b", re.I)),
    ("tenant_isolation_bypass", re.compile(r"\b(tenantId|tenant_id|orgId|organizationId|workspaceId|companyId|/tenant|/org/)\b", re.I)),
    ("admin_privilege_or_authorization_bypass", re.compile(r"\b(admin|roleId|role_id|isAdmin|permission|policy|guard|acl|rbac|abac)\b", re.I)),
    ("SSRF_or_open_redirect_candidate", re.compile(r"\b(callback|callbackUrl|callback_url|redirect|redirect_uri|returnUrl|avatarUrl|importUrl|webhook|url=|uri=)\b", re.I)),
    ("arbitrary_file_read_or_path_traversal", re.compile(r"\b(download|send_file|sendFile|filePath|filename|path=|\.\.\/|objectKey|bucket|export)\b", re.I)),
    ("arbitrary_file_write_or_upload_chain", re.compile(r"\b(upload|multipart|writeFile|putObject|archive|extract|destination|FormData)\b", re.I)),
    ("graphql_authorization_bypass", re.compile(r"\b(GraphQL|graphql|gql|mutation|subscription|resolver)\b", re.I)),
    ("websocket_authorization_bypass", re.compile(r"\b(WebSocket|websocket|socket\.on|ws\.on|EventSource|SSE|subscribe|channel)\b", re.I)),
    ("command_or_code_execution_candidate", re.compile(r"\b(eval|Function|child_process|exec\(|spawn\(|os\.system|subprocess|Runtime\.exec|pickle|unserialize|render_template_string)\b", re.I)),
    ("SQL_or_NoSQL_injection_candidate", re.compile(r"\b(raw_sql|whereRaw|query\(|execute\(|find\(|aggregate\(|\$where|orderBy|filter)\b", re.I)),
    ("sensitive_info_to_takeover_or_privilege", re.compile(r"\b(token|secret|api[_-]?key|password|session|cookie|Authorization|Bearer|PRIVATE KEY)\b", re.I)),
    ("cache_poisoning_or_cross_user_cache", re.compile(r"\b(cache|Cache-Control|Vary|cdn|surrogate|service-worker|precache|workbox)\b", re.I)),
]

PARAM_HINTS = ["tenantId", "tenant_id", "orgId", "organizationId", "userId", "user_id", "roleId", "role_id", "path", "file", "filename", "url", "callback", "redirect", "objectKey", "bucket"]
METHOD_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\b", re.I)
URL_RE = re.compile(r"(?P<url>https?://[^\s'\"<>]+|/[A-Za-z0-9_./{}:$?&=%+\-#]{2,})")

def stable_id(*parts: Any) -> str:
    return "IS-" + hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:14]

def load_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    for n, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                obj.setdefault("_input_file", str(path))
                obj.setdefault("_input_line", n)
                yield obj
        except json.JSONDecodeError:
            yield {"type": "unparsed_line", "value": line[:500], "_input_file": str(path), "_input_line": n}

def text_of(item: dict[str, Any]) -> str:
    return " ".join(str(item.get(k, "")) for k in ("type", "asset_type", "value", "endpoint", "path", "file", "source_file", "summary", "kind"))

def pick_endpoint(s: str) -> str | None:
    m = URL_RE.search(s)
    return m.group("url") if m else None

def pick_param(s: str) -> str | None:
    for p in PARAM_HINTS:
        if re.search(r"\b" + re.escape(p) + r"\b", s, re.I):
            return p
    qm = re.search(r"[?&]([A-Za-z0-9_]{2,40})=", s)
    return qm.group(1) if qm else None

def vulns_for(s: str) -> list[str]:
    out = []
    for name, rx in VULN_RULES:
        if rx.search(s):
            out.append(name)
    return sorted(set(out))

def auth_context(s: str) -> str:
    if re.search(r"\b(auth|authorization|bearer|cookie|session|csrf|jwt|login|withCredentials|permission|guard|policy)\b", s, re.I):
        return "auth_related_candidate"
    return "unknown"

def tenant_context(s: str) -> str:
    if re.search(r"\b(tenant|orgId|organizationId|workspace|companyId)\b", s, re.I):
        return "tenant_related_candidate"
    return "unknown"

def role_context(s: str) -> str:
    if re.search(r"\b(admin|role|permission|rbac|abac|acl)\b", s, re.I):
        return "role_related_candidate"
    return "unknown"

def normalize(item: dict[str, Any]) -> dict[str, Any]:
    s = text_of(item)
    ep = item.get("endpoint") or item.get("path") or item.get("url") or pick_endpoint(s)
    method = item.get("method")
    if not method:
        m = METHOD_RE.search(s)
        method = m.group(1).upper() if m else None
    source_file = item.get("source_file") or item.get("file") or item.get("path")
    line = item.get("line") or item.get("source_line")
    try:
        line = int(line) if line is not None else None
    except Exception:
        line = None
    vulns = vulns_for(s)
    review = "static_candidate"
    confidence = 0.35
    if vulns:
        review = "needs_review" if any(v in vulns for v in ["command_or_code_execution_candidate", "sensitive_info_to_takeover_or_privilege"]) else "promoted_candidate"
        confidence = 0.55
    if not source_file:
        review = "blocked"
        confidence = 0.1
    if item.get("dynamic_status") in {"runtime_accessible", "validated"}:
        confidence = min(0.85, confidence + 0.25)
    if auth_context(s) == "unknown" and any(v in vulns for v in ["IDOR/BOLA", "tenant_isolation_bypass", "admin_privilege_or_authorization_bypass"]):
        review = "needs_review"
    return {
        "schema_version": SCHEMA_VERSION,
        "asset_id": item.get("asset_id") or stable_id(source_file, line, item.get("type"), ep, item.get("value")),
        "source_file": source_file,
        "source_line": line,
        "source_type": item.get("type") or item.get("kind") or "unknown_candidate",
        "surface_type": item.get("asset_type") or item.get("type") or "unknown_surface",
        "endpoint": ep,
        "method": method,
        "parameter": pick_param(s),
        "auth_context": auth_context(s),
        "role_context": role_context(s),
        "tenant_context": tenant_context(s),
        "data_object": item.get("data_object") or None,
        "evidence": [{"input_file": item.get("_input_file"), "input_line": item.get("_input_line"), "raw_type": item.get("type"), "value_preview": str(item.get("value", ""))[:240]}],
        "candidate_vulnerability": vulns,
        "detector_route": "detectors/severe_vulnerability_matrix.yaml" if vulns else None,
        "report_template": TEMPLATE if vulns else None,
        "review_status": review,
        "evidence_status": "merged_candidate",
        "confidence": confidence,
        "dynamic_status": item.get("dynamic_status") or "not_validated",
        "quality_gate": {"dynamic_evidence_required": "PASS" if item.get("dynamic_status") in {"runtime_accessible", "validated"} else "UNKNOWN"},
        "notes": "Candidate only. Promotion requires authorized runtime evidence, role/tenant context when applicable, QG and human review."
    }

def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize local information collection candidates and map them to severe-vulnerability entry signals.")
    ap.add_argument("--input", action="append", required=True, help="JSONL candidate file from local authorized analysis")
    ap.add_argument("-o", "--output", default="info-surface.normalized.jsonl")
    args = ap.parse_args()
    out_count = 0
    seen: set[tuple[Any, ...]] = set()
    with Path(args.output).open("w", encoding="utf-8") as wf:
        for inp in args.input:
            for item in load_jsonl(Path(inp)):
                row = normalize(item)
                key = (row["source_file"], row["source_line"], row["source_type"], row["endpoint"], row["parameter"])
                if key in seen:
                    continue
                seen.add(key)
                wf.write(json.dumps(row, ensure_ascii=False) + "\n")
                out_count += 1
    print(f"wrote {out_count} normalized surface rows to {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
