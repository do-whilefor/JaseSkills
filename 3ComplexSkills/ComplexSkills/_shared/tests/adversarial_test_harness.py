#!/usr/bin/env python3
"""Semantic replay harness for local authorized skills package.

Validates real JSON Schema conformance, template dispatch, state semantics, executable
quality gate recomputation, and smoke-runs the 03/05 extractors on local fixtures.
"""
from __future__ import annotations
import importlib.util, json, subprocess, sys, tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "_shared" / "evidence" / "EVIDENCE_MANIFEST_SCHEMA.v4.1.json"
QG_PATH = ROOT / "_shared" / "quality" / "quality_gate_v4_1.py"

try:
    import jsonschema  # type: ignore
except Exception as exc:  # pragma: no cover
    jsonschema = None
    JSONSCHEMA_IMPORT_ERROR = str(exc)
else:
    JSONSCHEMA_IMPORT_ERROR = ""

spec = importlib.util.spec_from_file_location("quality_gate_v4_1", QG_PATH)
qg = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(qg)  # type: ignore

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def validate_schema(obj: dict[str, Any], errors: list[str], case_id: str) -> None:
    if jsonschema is None:
        errors.append(f"{case_id}: jsonschema package missing: {JSONSCHEMA_IMPORT_ERROR}")
        return
    schema = load_json(SCHEMA)
    validator = jsonschema.Draft202012Validator(schema)
    for e in sorted(validator.iter_errors(obj), key=lambda e: list(e.absolute_path)):
        errors.append(f"{case_id}: schema error at {'.'.join(map(str,e.absolute_path)) or '<root>'}: {e.message}")

def template_lookup() -> dict[str, Any]:
    idx = load_json(ROOT / "_shared" / "template_index.json")
    return {t["template_id"]: t for t in idx.get("templates", [])}

def validate_case(case: dict[str, Any], templates: dict[str, Any], errors: list[str], stats: dict[str, int]) -> None:
    cid = case.get("id", "<no-id>")
    fpath = TEST_ROOT / case.get("input_fixture", "")
    if not fpath.exists():
        errors.append(f"{cid}: missing fixture {fpath}"); return
    fx = load_json(fpath)
    validate_schema(fx, errors, cid)
    tid = case.get("template_id") or fx.get("template_id")
    if tid not in templates:
        errors.append(f"{cid}: template_id not indexed: {tid}"); return
    tpl = templates[tid]
    # Template dispatch must bind every replay type.
    replay_paths = set((tpl.get("replay_fixtures") or {}).values())
    rel = "_shared/tests/" + case.get("input_fixture")
    if rel not in replay_paths:
        errors.append(f"{cid}: fixture not bound in template_index replay_fixtures: {rel}")
    # Required files must exist.
    for key in ["evidence_fields","dynamic_boundary","negative_controls","report_template","quality_overlay"]:
        p = ROOT / tpl.get(key, "")
        if not p.exists(): errors.append(f"{cid}: template missing {key}: {p}")
    # Specialized fields must match template requirements.
    fields = (fx.get("specialized_evidence") or {}).get("fields") or {}
    missing = [x for x in tpl.get("required_specialized_fields", []) if not fields.get(x)]
    if missing: errors.append(f"{cid}: missing specialized fields {missing}")
    # State/status semantics.
    expected = case.get("expected_status") or fx.get("expected_status")
    if fx.get("final_status") != expected:
        errors.append(f"{cid}: final_status {fx.get('final_status')} != expected {expected}")
    expected_state = {"confirmed":"confirmed","rejected":"rejected","blocked":"validation_blocked","needs_human_review":"needs_human_review"}.get(expected)
    if expected_state and fx.get("state") != expected_state:
        errors.append(f"{cid}: state {fx.get('state')} != {expected_state}")
    # Executable QG recompute.
    result = qg.compute_quality(fx, SCHEMA)
    if result.get('checks', {}).get('state_machine_valid') is not True:
        errors.append(f"{cid}: state machine invalid: {result.get('reasons')[:5]}")
    if result.get('checks', {}).get('artifact_hashes_valid') is not True and expected == 'confirmed':
        errors.append(f"{cid}: confirmed fixture artifact hashes invalid: {result.get('reasons')[:5]}")
    if not result.get("schema_valid"):
        errors.append(f"{cid}: quality gate schema invalid: {result.get('reasons')[:3]}")
    if expected == "confirmed" and not result.get("passed"):
        errors.append(f"{cid}: confirmed fixture did not pass executable quality gate: {result}")
    if expected in {"rejected","blocked"} and result.get("passed"):
        errors.append(f"{cid}: {expected} fixture unexpectedly passed quality gate")
    if expected == "needs_human_review" and fx.get("final_status") == "confirmed":
        errors.append(f"{cid}: review fixture became confirmed")
    stats[expected] = stats.get(expected, 0) + 1

def run_extractor_smoke(errors: list[str]) -> dict[str, Any]:
    sample = ROOT / "_shared" / "tests" / "samples" / "fixture_project"
    results: dict[str, Any] = {}
    cmds = {
        "03": [sys.executable, str(ROOT / "skills" / "03-code-knowledge-graph" / "scripts" / "advanced_code_graph_extractor.py"), str(sample)],
        "05": [sys.executable, str(ROOT / "skills" / "05-js-audit-runtime" / "scripts" / "advanced_js_runtime_extractor.py"), str(sample)],
    }
    for key, cmd in cmds.items():
        cp = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if cp.returncode != 0:
            errors.append(f"extractor {key} failed: {cp.stderr[:300]}"); continue
        try: data = json.loads(cp.stdout)
        except Exception as exc:
            errors.append(f"extractor {key} non-json output: {exc}"); continue
        results[key] = {"route_count": len(data.get("routes", [])), "api_client_count": len(data.get("api_clients", [])), "source_map_count": len(data.get("source_maps", [])), "candidate_signal_count": len(data.get("candidate_signals", []))}
    if results.get("03", {}).get("route_count", 0) < 2:
        errors.append("extractor 03 did not extract expected local fixture routes")
    if results.get("05", {}).get("api_client_count", 0) < 2 or results.get("05", {}).get("source_map_count", 0) < 1:
        errors.append("extractor 05 did not extract expected JS API clients and sourcemap data")
    return results


def run_adversarial_regression_tests(errors: list[str]) -> dict[str, Any]:
    path = TEST_ROOT / "adversarial_regression_tests.json"
    if not path.exists():
        errors.append("missing adversarial_regression_tests.json")
        return {"case_count": 0}
    cases = load_json(path)
    checked = 0
    for i, case in enumerate(cases):
        cid = case.get('id', f'adversarial-{i}')
        # Regression cases are contract tests for routing and hallucination guards.
        if 'id' not in case:
            errors.append(f"{cid}: missing adversarial field id")
        if not (case.get('input_fixture') or case.get('input')):
            errors.append(f"{cid}: missing adversarial input_fixture or input")
        behavior_blob = json.dumps(case, ensure_ascii=False).lower()
        if not any(x in behavior_blob for x in ['forbid_status', 'must_not_confirm','reject','rejected','block','blocked','needs_human_review','candidate_only','do_not_execute']):
            errors.append(f"{cid}: expected behavior must include fail-closed/candidate-only assertion")
        if 'confirmed' not in behavior_blob:
            errors.append(f"{cid}: adversarial case must explicitly forbid or avoid confirmed status")
        checked += 1
    return {"case_count": checked}


def run_candidate_engine_per_template_replay(errors: list[str]) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("vulnerability_candidate_engine", ROOT / "skills" / "07-vulnerability-hunting-engine" / "scripts" / "vulnerability_candidate_engine.py")
    mod = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
    index_path = TEST_ROOT / "candidate_engine_per_template_replay_index.json"
    index = load_json(index_path)
    pos_ok = 0; neg_ok = 0
    for entry in index:
        tid = entry['template_id']
        pos = load_json(ROOT / entry['positive'])['input']
        res = mod.generate(pos.get('code_graph',{}), pos.get('js_audit',{}), pos.get('surface',{}), pos.get('inventory',{}))
        tids = {c.get('template_id') for c in res.get('candidates', [])}
        if tid not in tids:
            errors.append(f"candidate positive replay failed for {tid}: produced {sorted(tids)}")
        else:
            pos_ok += 1
        neg = load_json(ROOT / entry['negative'])['input']
        resn = mod.generate(neg.get('code_graph',{}), neg.get('js_audit',{}), neg.get('surface',{}), neg.get('inventory',{}))
        tidsn = {c.get('template_id') for c in resn.get('candidates', [])}
        if tid in tidsn:
            errors.append(f"candidate negative replay produced forbidden template {tid}")
        else:
            neg_ok += 1
    return {"positive_passed": pos_ok, "negative_passed": neg_ok, "template_count": len(index)}


def main() -> int:
    errors: list[str] = []
    stats: dict[str, int] = {}
    templates = template_lookup()
    if len(templates) != 23:
        errors.append(f"expected 23 templates, got {len(templates)}")
    cases = load_json(TEST_ROOT / "canonical_replay_cases.json")
    if len(cases) != 92:
        errors.append(f"expected 92 canonical replay cases, got {len(cases)}")
    for c in cases:
        validate_case(c, templates, errors, stats)
    extractor_results = run_extractor_smoke(errors)
    adversarial_results = run_adversarial_regression_tests(errors)
    candidate_replay = run_candidate_engine_per_template_replay(errors)
    result = {"passed": not errors, "case_count": len(cases), "adversarial_regression": adversarial_results, "candidate_engine_per_template_replay": candidate_replay, "template_count": len(templates), "status_counts": stats, "extractor_smoke": extractor_results, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
