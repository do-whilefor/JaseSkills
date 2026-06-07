#!/usr/bin/env python3
"""Runtime probes and adapter contract for full parser backends v4.3.

This module does not pretend that JavaParser/PHP-Parser/Rust syn/tree-sitter are
installed. A language backend can be promoted only when this probe returns
runtime_ready=true and parser_confidence=full_ast. AST-lite remains candidate-only.
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
BACKEND_ROOT = Path(__file__).resolve().parent

LANGUAGES = {
  "java": {"backend": "javaparser", "required": ["java"], "env": "JAVAPARSER_CLI", "bridge": "java_javaparser_bridge.py"},
  "php": {"backend": "nikic_php_parser", "required": ["php"], "env": "PHP_PARSER_BRIDGE", "bridge": "php_parser_bridge.php"},
  "go": {"backend": "go_parser", "required": ["go"], "env": "GO_PARSER_BRIDGE", "bridge": "go_parser_bridge.go"},
  "rust": {"backend": "rust_syn", "required": ["cargo", "rustc"], "env": "RUST_SYN_BRIDGE", "bridge": "rust_syn_bridge/Cargo.toml"},
  "ruby": {"backend": "ruby_ripper", "required": ["ruby"], "env": "RUBY_RIPPER_BRIDGE", "bridge": "ruby_ripper_bridge.rb"},
}

def cmd_exists(cmd: str) -> bool:
    return bool(shutil.which(cmd))

def run(cmd: list[str], timeout: int = 15) -> tuple[bool, str]:
    try:
        cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return cp.returncode == 0, (cp.stdout + cp.stderr).strip()[:1000]
    except Exception as exc:
        return False, f"{exc.__class__.__name__}: {exc}"

def probe_language(lang: str) -> dict[str, Any]:
    spec = LANGUAGES[lang]
    missing = [c for c in spec["required"] if not cmd_exists(c)]
    bridge_path = BACKEND_ROOT / spec["bridge"]
    env_override = os.environ.get(spec["env"])
    errors: list[str] = []
    if missing:
        errors.append("missing commands: " + ",".join(missing))
    if lang in {"java", "php", "rust"} and not env_override and not bridge_path.exists():
        errors.append("missing bridge or env override")
    smoke_ready = False
    smoke_reason = "not_executed"
    if not errors:
        if lang == "ruby":
            smoke_ready, smoke_reason = run(["ruby", "-rripper", "-e", "p Ripper.sexp('class A; def b; end; end') != nil"], 10)
        elif lang == "go":
            smoke = BACKEND_ROOT / "go_parser_bridge.go"
            smoke_ready, smoke_reason = run(["go", "run", str(smoke), "--probe"], 20)
        elif lang == "php":
            bridge = env_override or str(BACKEND_ROOT / "php_parser_bridge.php")
            smoke_ready, smoke_reason = run(["php", bridge, "--probe"], 20)
        elif lang == "java":
            if env_override:
                smoke_ready, smoke_reason = run(["java", "-jar", env_override, "--probe"], 20)
            else:
                smoke_ready, smoke_reason = False, "JAVAPARSER_CLI env not set to JavaParser CLI jar"
        elif lang == "rust":
            bridge_dir = env_override or str(BACKEND_ROOT / "rust_syn_bridge")
            smoke_ready, smoke_reason = run(["cargo", "run", "--quiet", "--manifest-path", str(Path(bridge_dir) / "Cargo.toml"), "--", "--probe"], 45)
    runtime_ready = (not errors) and smoke_ready
    return {
      "language": lang,
      "backend": spec["backend"],
      "runtime_ready": bool(runtime_ready),
      "command_status": {c: cmd_exists(c) for c in spec["required"]},
      "bridge_path": str(bridge_path.relative_to(ROOT)) if bridge_path.exists() else None,
      "env_override": bool(env_override),
      "smoke_probe_passed": bool(smoke_ready),
      "smoke_reason": smoke_reason,
      "promotion_status": "promoted_allowed" if runtime_ready else "blocked_until_runtime_ready",
      "parser_confidence": "full_ast" if runtime_ready else "manual_required",
      "claim_policy": "Only runtime_ready=true may satisfy promoted/full AST claims; otherwise AST-lite outputs are candidate-only."
    }

def probe_all() -> dict[str, Any]:
    rows = [probe_language(lang) for lang in LANGUAGES]
    return {
      "schema_version": "parser_runtime_readiness_v4.3",
      "read_only": True,
      "runtime_ready_count": sum(1 for r in rows if r["runtime_ready"]),
      "required_full_ast_languages": list(LANGUAGES),
      "languages": rows,
      "all_full_backends_ready": all(r["runtime_ready"] for r in rows),
      "promotion_rule": "Java/PHP/Go/Rust/Ruby cannot be promoted unless their own runtime_ready=true."
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--language", choices=list(LANGUAGES))
    ap.add_argument("--out")
    args = ap.parse_args()
    res = probe_language(args.language) if args.language else probe_all()
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
