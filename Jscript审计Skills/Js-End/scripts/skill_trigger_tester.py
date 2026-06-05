#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root/"scripts"))
from skill_dispatcher import route
cases = json.loads((root/"tests/trigger-test-cases.json").read_text(encoding="utf-8"))
failed = 0
for c in cases:
    ctx = ["js_security_context"] if c.get("context") else []
    data = route(c["input"], ctx)
    chain = data.get("chain", [])
    ok = all(x in chain for x in c.get("expected_chain", [])) and all(x not in chain for x in c.get("not_expected", []))
    if not ok:
        failed += 1
    print(json.dumps({"name": c["name"], "chain": chain, "expected": c.get("expected_chain", []), "not_expected": c.get("not_expected", []), "ok": ok}, ensure_ascii=False))
raise SystemExit(1 if failed else 0)
