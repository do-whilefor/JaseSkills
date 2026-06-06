#!/usr/bin/env python3
"""Build role/tenant authorization replay matrix from local attack surface data."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any

AUTHZ_RE = re.compile(r"(?i)(admin|owner|member|tenant|role|permission|authz|policy|guard|acl|rbac|readonly|read_only|super)")
ID_RE = re.compile(r"(?i)(^|[_/-])(id|uuid|user_id|tenant_id|org_id|project_id|account_id|owner_id)($|[_/-])")
DEFAULT_ROLES = ["anonymous", "readonly", "member", "owner", "admin"]
DEFAULT_TENANTS = ["tenant_a", "tenant_b"]


def load(path: str | None) -> Any:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {"_missing": str(p)}
    return json.loads(p.read_text(encoding="utf-8", errors="ignore"))


def rows_from_surface(obj: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    def rec(x: Any) -> None:
        if isinstance(x, dict):
            route = x.get("route") or x.get("path") or x.get("url") or x.get("api") or x.get("target")
            method = x.get("method") or x.get("http_method") or "ANY"
            file = x.get("file") or x.get("source_file") or ""
            line = x.get("line") or x.get("line_start") or None
            blob = json.dumps(x, ensure_ascii=False)
            if route or AUTHZ_RE.search(blob) or ID_RE.search(blob):
                rows.append({"route": route or "<unknown>", "method": method, "file": file, "line": line, "authz_signal": bool(AUTHZ_RE.search(blob)), "object_id_signal": bool(ID_RE.search(blob)), "raw_signal": blob[:1000]})
            for v in x.values():
                rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)
    rec(obj)
    seen = set(); out = []
    for r in rows:
        key = (r.get("route"), r.get("method"), r.get("file"), r.get("line"))
        if key in seen:
            continue
        seen.add(key); out.append(r)
    return out


def build(args: argparse.Namespace) -> dict[str, Any]:
    surface = load(args.surface)
    candidates = load(args.candidates)
    account = load(args.account_matrix)
    roles = account.get("roles") if isinstance(account, dict) else None
    tenants = account.get("tenants") if isinstance(account, dict) else None
    roles = roles or DEFAULT_ROLES
    tenants = tenants or DEFAULT_TENANTS
    route_rows = rows_from_surface(surface) + rows_from_surface(candidates)
    matrix = []
    for r in route_rows:
        route = str(r.get("route") or "")
        interesting = r.get("authz_signal") or r.get("object_id_signal") or re.search(r"(?i)/(admin|api|internal|graphql|v\d+|legacy|export|download|share|archive|delete|update|copy)", route)
        if not interesting:
            continue
        for role in roles:
            for tenant in tenants:
                for replay_role in roles:
                    if replay_role == role:
                        continue
                    matrix.append({"route": r.get("route"), "method": r.get("method"), "file": r.get("file"), "line": r.get("line"), "baseline_role": role, "baseline_tenant": tenant, "replay_role": replay_role, "replay_tenant": tenant, "control_type": "role_negative_control", "expected": "same_or_less_privilege_than_baseline; no cross-role escalation", "non_destructive": True})
                for replay_tenant in tenants:
                    if replay_tenant == tenant:
                        continue
                    matrix.append({"route": r.get("route"), "method": r.get("method"), "file": r.get("file"), "line": r.get("line"), "baseline_role": role, "baseline_tenant": tenant, "replay_role": role, "replay_tenant": replay_tenant, "control_type": "tenant_negative_control", "expected": "cross-tenant object access must be denied or empty", "non_destructive": True})
    return {"schema_version": "role_tenant_authz_matrix_v1", "non_destructive": True, "roles": roles, "tenants": tenants, "surface_count": len(route_rows), "test_case_count": len(matrix), "test_cases": matrix, "promotion_policy": "authz/IDOR/tenant/admin claims require executed positive and negative rows from this matrix", "status": "planned_only_until_executed"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface")
    ap.add_argument("--candidates")
    ap.add_argument("--account-matrix")
    ap.add_argument("--out")
    args = ap.parse_args()
    result = build(args)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
