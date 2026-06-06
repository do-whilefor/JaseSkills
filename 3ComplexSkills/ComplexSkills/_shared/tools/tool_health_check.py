#!/usr/bin/env python3
"""Runtime tool health probe for the authorized local security audit skills package."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUS_ENUM = ["ready", "degraded", "missing", "failed", "manual_required"]

COMMAND_CHECKS = [
    ("Python runtime", "language", sys.executable, [sys.executable, "--version"]),
    ("Node runtime", "language", "node", ["node", "--version"]),
    ("Java runtime", "language", "java", ["java", "-version"]),
    ("PHP runtime", "language", "php", ["php", "--version"]),
    ("Go runtime", "language", "go", ["go", "version"]),
    ("Rust/Cargo", "language", "cargo", ["cargo", "--version"]),
    ("tree-sitter CLI", "ast", "tree-sitter", ["tree-sitter", "--version"]),
]

PY_PACKAGE_CHECKS = [
    ("Playwright Python package", "dynamic", "playwright"),
]

NODE_PACKAGE_CHECKS = [
    ("Babel parser", "ast", "@babel/parser"),
    ("TypeScript Compiler API package", "ast", "typescript"),
]

MANUAL_CHECKS = [
    ("JavaParser library/CLI", "ast", "manual_required", "Confirm javaparser JAR/CLI path locally before using Java AST mode."),
    ("PHP-Parser", "ast", "manual_required", "Confirm nikic/PHP-Parser or equivalent before using PHP AST mode."),
    ("Rust syn", "ast", "manual_required", "Confirm Rust syn parser integration before using Rust AST mode."),
    ("MCP config", "dynamic", "manual_required", "Confirm MCP endpoint/config before using MCP capture."),
    ("Browser executable", "dynamic", "manual_required", "Confirm chromium/msedge/firefox path before real browser capture."),
]


def command_check(display: str, category: str, cmd: str, probe: list[str]) -> dict:
    path = cmd if cmd == sys.executable else shutil.which(cmd)
    if not path:
        return {"name": display, "category": category, "status": "missing", "detail": f"{cmd} not found", "verification_mode": "runtime_probe"}
    try:
        proc = subprocess.run(probe, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
        detail = (proc.stdout or proc.stderr).strip().splitlines()[0] if (proc.stdout or proc.stderr).strip() else path
        status = "ready" if proc.returncode == 0 else "degraded"
    except Exception as exc:
        detail = f"{path}; probe failed: {exc.__class__.__name__}"
        status = "degraded"
    return {"name": display, "category": category, "status": status, "detail": detail, "path": path, "verification_mode": "runtime_probe"}


def py_pkg_check(display: str, category: str, pkg: str) -> dict:
    spec = importlib.util.find_spec(pkg)
    if not spec:
        return {"name": display, "category": category, "status": "missing", "detail": f"python package {pkg} not importable", "verification_mode": "runtime_probe"}
    return {"name": display, "category": category, "status": "ready", "detail": str(spec.origin), "verification_mode": "runtime_probe"}


def node_pkg_check(display: str, category: str, pkg: str) -> dict:
    if not shutil.which("node"):
        return {"name": display, "category": category, "status": "missing", "detail": "node not found", "verification_mode": "runtime_probe"}
    script = f"require.resolve('{pkg}')"
    proc = subprocess.run(["node", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=3)
    if proc.returncode == 0:
        return {"name": display, "category": category, "status": "ready", "detail": proc.stdout.strip(), "verification_mode": "runtime_probe"}
    return {"name": display, "category": category, "status": "missing", "detail": f"node package {pkg} not resolvable", "verification_mode": "runtime_probe"}


def check_port(name: str, category: str, host: str, port: int) -> dict:
    s = socket.socket(); s.settimeout(0.4)
    try:
        s.connect((host, port))
        return {"name": name, "category": category, "status": "degraded", "detail": f"{host}:{port} open but Burp API/CA/project context not verified", "verification_mode": "port_probe_only"}
    except Exception as exc:
        return {"name": name, "category": category, "status": "degraded", "detail": f"{host}:{port} unavailable: {exc.__class__.__name__}", "verification_mode": "runtime_probe"}
    finally:
        s.close()


def build_result() -> dict:
    checks = []
    command_checks = list(COMMAND_CHECKS)
    if os.name == "nt":
        command_checks.insert(1, ("Python launcher", "language", "py", ["py", "-3", "--version"]))
    for item in command_checks:
        checks.append(command_check(*item))
    for item in PY_PACKAGE_CHECKS:
        checks.append(py_pkg_check(*item))
    for item in NODE_PACKAGE_CHECKS:
        checks.append(node_pkg_check(*item))
    checks.append(check_port("Burp proxy localhost:8080", "dynamic", "127.0.0.1", 8080))
    for name, category, status, detail in MANUAL_CHECKS:
        checks.append({"name": name, "category": category, "status": status, "detail": detail, "verification_mode": "manual_required"})
    ready = sum(1 for c in checks if c["status"] == "ready")
    total = len(checks)
    return {
        "score": round(100 * ready / total),
        "ready_count": ready,
        "total_checks": total,
        "checks": checks,
        "status_enum": STATUS_ENUM,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verification_mode": "runtime_probe_with_manual_required",
        "policy": "This file is a runtime snapshot. Re-run tool_health_check.py on the target workstation before relying on tool availability.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", help="write JSON snapshot to this path")
    args = ap.parse_args()
    result = build_result()
    if args.write:
        out = Path(args.write)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
