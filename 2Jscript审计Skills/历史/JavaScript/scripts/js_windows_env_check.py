#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, platform, re, shutil, subprocess, sys
from pathlib import Path

PY = sys.executable


def run(cmd, cwd: Path, timeout=30):
    try:
        p = subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"cmd": cmd, "returncode": p.returncode, "ok": p.returncode == 0, "stdout_tail": p.stdout[-2000:], "stderr_tail": p.stderr[-2000:]}
    except Exception as e:
        return {"cmd": cmd, "returncode": 127, "ok": False, "error": str(e)}


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def grep_hardcoded_python3(root: Path):
    findings = []
    for rel_root in ["package.json", "scripts"]:
        base = root / rel_root
        files = [base] if base.is_file() else list(base.rglob("*.py")) + list(base.rglob("*.mjs"))
        for p in files:
            if p.name in {'js_windows_env_check.py', 'js_cross_platform_runner.mjs'}:
                continue
            txt = p.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(txt.splitlines(), 1):
                if "python3" in line and "#!/usr/bin/env python3" not in line:
                    findings.append({"file": str(p.relative_to(root)), "line": i, "text": line[:240]})
    return findings


def grep_posix_only_runtime(root: Path):
    patterns = [
        ("timeout command", re.compile(r"\['timeout'|\btimeout\s+\d+")),
        ("bash invocation", re.compile(r"\bbash\b|sh\s+-c")),
        ("/tmp absolute path", re.compile(r"/tmp/")),
        ("/usr/bin/chromium hard requirement", re.compile(r"/usr/bin/chromium")),
    ]
    findings = []
    for p in list((root / "scripts").rglob("*.py")) + list((root / "scripts").rglob("*.mjs")) + [root / "package.json"]:
        if p.name == 'js_windows_env_check.py':
            continue
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(txt.splitlines(), 1):
            for name, pat in patterns:
                if pat.search(line):
                    findings.append({"kind": name, "file": str(p.relative_to(root)), "line": i, "text": line[:240]})
    return findings


def check_wrappers(root: Path):
    required = [
        "tools/windows/install.ps1",
        "tools/windows/validate.ps1",
        "tools/windows/import-authorized-target.ps1",
        "tools/windows/run.cmd",
        "tools/windows/validate.cmd",
        "scripts/js_cross_platform_runner.mjs",
        "scripts/js_windows_validation_suite.py",
    ]
    return [{"path": r, "exists": (root / r).exists()} for r in required]


def main():
    ap = argparse.ArgumentParser(description="Windows readiness check for JS-End skills. It does not claim that a browser replay succeeded unless artifacts exist.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="reports/windows-check")
    ap.add_argument("--simulate-windows", action="store_true", help="Check Windows compatibility from any OS without claiming runtime replay execution on Windows.")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    out = (root / args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    package = load_json(root / "package.json")
    scripts = package.get("scripts", {})
    hardcoded_python3 = grep_hardcoded_python3(root)
    posix_only = grep_posix_only_runtime(root)
    wrappers = check_wrappers(root)
    binaries = []
    for name in ["node", "npm", "npx", "git"]:
        binaries.append({"name": name, "path": shutil.which(name), "ok": bool(shutil.which(name))})
    binaries.append({"name": "python-current", "path": PY, "ok": Path(PY).exists()})
    node_runner_help = run(["node", "scripts/js_cross_platform_runner.mjs", "--help"], root) if shutil.which("node") else {"ok": False, "error": "node missing"}
    python_version = run([PY, "--version"], root)
    npm_windows_validate_present = scripts.get("windows:validate") == "node scripts/js_cross_platform_runner.mjs windows:validate"
    npm_p1_uses_runner = scripts.get("p1:validate") == "node scripts/js_cross_platform_runner.mjs p1:validate"
    ok = (
        all(w["exists"] for w in wrappers)
        and not hardcoded_python3
        and not [f for f in posix_only if f["kind"] in {"timeout command", "bash invocation"}]
        and npm_windows_validate_present
        and npm_p1_uses_runner
        and bool(node_runner_help.get("ok"))
        and bool(python_version.get("ok"))
    )
    result = {
        "schema_version": "js-windows-env-check/v1",
        "ok": ok,
        "host_platform": platform.platform(),
        "simulate_windows": bool(args.simulate_windows),
        "windows_runtime_claim": "not-run-on-windows" if os.name != "nt" else "ran-on-windows-host",
        "python_executable": PY,
        "package_scripts_checked": sorted(scripts.keys()),
        "binaries": binaries,
        "wrappers": wrappers,
        "node_runner_help": node_runner_help,
        "python_version": python_version,
        "hardcoded_python3": hardcoded_python3,
        "posix_only_findings": posix_only,
        "quality_rules": [
            "Windows readiness is ready only for command portability; browser execution remains blocked unless Playwright artifacts are produced.",
            "Fixture runtime evidence cannot satisfy authorized target import gate.",
            "Confirmed findings require request/response and runtime artifact binding."
        ],
    }
    (out / "js_windows_env_check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "out": str(out / "js_windows_env_check.json"), "hardcoded_python3": len(hardcoded_python3), "posix_only": len(posix_only)}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
