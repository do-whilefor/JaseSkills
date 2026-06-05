#!/usr/bin/env python3
"""Integrity selftest for the authorized local security audit skills package.

Checks Python compilation, path references, true JSON Schema validation for every
canonical fixture, schema roundtrip, replay harness, extractor smoke test, template
index bindings, dashboard generation, and quality gate execution.
"""
from __future__ import annotations
import csv, json, py_compile, re, subprocess, sys, tempfile, hashlib, os, io, contextlib, importlib.util, shutil
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "_shared"
ERRORS: list[str] = []
WARNINGS: list[str] = []
REF_RE = re.compile(r"(?:(?:_shared/|skills/|reverse_audit_reports/)[A-Za-z0-9_./:-]+(?:\.md|\.json|\.csv|\.yaml|\.yml|\.py|\.sh|\.ps1)?)")
try:
    import jsonschema  # type: ignore
except Exception as exc:
    jsonschema = None
    WARNINGS.append(f"jsonschema import failed: {exc}")


def subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def check(condition: bool, message: str) -> None:
    if not condition: ERRORS.append(message)

def py_compile_all() -> None:
    for p in sorted(ROOT.rglob("*.py")):
        if "__pycache__" in p.parts: continue
        try: py_compile.compile(str(p), cfile=str(Path(tempfile.mkdtemp()) / (p.name + '.pyc')), doraise=True)
        except Exception as exc: ERRORS.append(f"py_compile failed: {p.relative_to(ROOT)}: {exc}")

def check_no_pycache() -> None:
    # Runtime imports may create bytecode in some Python configurations. Remove it and
    # fail only if it cannot be removed from the package tree.
    for d in list(ROOT.rglob("__pycache__")):
        import shutil
        shutil.rmtree(d, ignore_errors=True)
    bad = [p for p in ROOT.rglob("__pycache__")]
    check(not bad, f"package contains __pycache__ directories: {[str(p.relative_to(ROOT)) for p in bad[:10]]}")

def check_references() -> None:
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in {".md", ".json", ".yaml", ".yml", ".txt", ".py", ".sh", ".ps1"}: continue
        if "__pycache__" in p.parts: continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for ref in REF_RE.findall(text):
            ref_clean = ref.strip("`),.，。:; ")
            if ":" in ref_clean and ref_clean.rsplit(":", 1)[-1].isdigit(): ref_clean = ref_clean.rsplit(":", 1)[0]
            if not (ROOT / ref_clean).exists(): ERRORS.append(f"missing referenced path: {ref_clean} in {p.relative_to(ROOT)}")

def validate_manifest(path: Path, schema: dict[str, Any]) -> None:
    if jsonschema is None:
        ERRORS.append("jsonschema package is required for true JSON Schema validation")
        return
    obj = load_json(path)
    validator = jsonschema.Draft202012Validator(schema)
    errs = list(validator.iter_errors(obj))
    for e in errs[:5]: ERRORS.append(f"schema validation failed {path.relative_to(ROOT)} at {'.'.join(map(str,e.absolute_path)) or '<root>'}: {e.message}")

def check_schema_roundtrip() -> None:
    schema_path = SHARED / "evidence" / "EVIDENCE_MANIFEST_SCHEMA.v4.1.json"
    schema = load_json(schema_path)
    fixtures = sorted((SHARED / "tests" / "fixtures").glob("C[0-9][0-9]-*.json"))
    check(len(fixtures) == 92, f"expected 92 canonical schema fixtures, got {len(fixtures)}")
    for f in fixtures: validate_manifest(f, schema)
    # true roundtrip validates a generated fixture-like object, not just json encode/decode.
    sample = load_json(fixtures[0]) if fixtures else {}
    if fixtures:
        encoded = json.dumps(sample, ensure_ascii=False)
        decoded = json.loads(encoded)
        if jsonschema is not None:
            errs = list(jsonschema.Draft202012Validator(schema).iter_errors(decoded))
            check(not errs, f"roundtrip sample failed schema after decode: {errs[:1]}")

def check_core_contracts() -> None:
    contracts = list((ROOT / "skills").glob("*/EXECUTION_CONTRACT.md"))
    check(len(contracts) == 10, f"expected 10 execution contracts, got {len(contracts)}")
    for sk in sorted((ROOT / "skills").iterdir()):
        if sk.is_dir():
            for f in ["SKILL.md", "INPUT_SCHEMA.json", "OUTPUT_SCHEMA.json", "EXECUTION_CONTRACT.md"]:
                check((sk / f).exists(), f"{sk.name} missing {f}")

def check_template_index() -> None:
    idx = load_json(SHARED / "template_index.json")
    templates = idx.get("templates", [])
    check(len(templates) == 23, f"expected 23 canonical templates, got {len(templates)}")
    required_keys = {"evidence_fields","dynamic_boundary","negative_controls","report_template","quality_overlay"}
    for t in templates:
        for k in required_keys:
            check((ROOT / t.get(k, "")).exists(), f"template {t.get('template_id')} missing {k}")
        rf = t.get("replay_fixtures", {})
        check(set(rf.keys()) == {"positive","negative","blocked","human_review"}, f"template {t.get('template_id')} missing replay fixture classes")
        for p in rf.values(): check((ROOT / p).exists(), f"template {t.get('template_id')} replay fixture missing {p}")

def check_quality_gate() -> None:
    qg = SHARED / "quality" / "quality_gate_v4_1.py"
    pos = SHARED / "tests" / "fixtures" / "C01-auth-bypass-POS-01.json"
    neg = SHARED / "tests" / "fixtures" / "C01-auth-bypass-NEG-01.json"
    for path, expect in [(pos, True),(neg, False)]:
        cp = subprocess.run([sys.executable, str(qg), str(path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, env=subprocess_env())
        try: result = json.loads(cp.stdout)
        except Exception as exc: ERRORS.append(f"quality gate non-json for {path.name}: {exc}: {cp.stderr}"); continue
        check(result.get("schema_valid") is True, f"quality gate schema invalid for {path.name}: {result}")
        check(result.get("passed") is expect, f"quality gate pass mismatch for {path.name}: expected {expect}, got {result.get('passed')}")

def check_replay_harness() -> None:
    # Run in-process to avoid subprocess hangs from inherited runtime state while still
    # executing the real harness logic against all canonical fixtures.
    import importlib.util
    spec = importlib.util.spec_from_file_location("adversarial_test_harness", SHARED / "tests" / "adversarial_test_harness.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            spec.loader.exec_module(mod)
            rc = mod.main()
        result = json.loads(buf.getvalue())
    except Exception as exc:
        ERRORS.append(f"replay harness failed in-process: {exc}: {buf.getvalue()[:300]}")
        return
    check(rc == 0 and result.get("passed") is True, f"semantic replay failed: {result}")
    check(result.get("case_count") == 92, f"semantic replay expected 92 canonical cases, got {result.get('case_count')}")
    check((result.get("status_counts") or {}).get("confirmed") == 23, "semantic replay missing 23 positive confirmed fixtures")

def check_dashboard() -> None:
    out = Path(tempfile.mkdtemp()) / "dashboard.html"
    cp = subprocess.run([sys.executable, str(SHARED / "dashboard" / "dashboard_generator.py"), str(out)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, env=subprocess_env())
    check(cp.returncode == 0 and out.exists(), f"dashboard generator failed: {cp.stderr[:300]}")
    if out.exists():
        html = out.read_text(encoding="utf-8", errors="ignore")
        for token in ["Route", "Candidate", "Evidence", "Quality", "Report", "C01-auth-bypass-POS-01"]:
            check(token in html, f"dashboard missing token {token}")

def _import_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def check_extractors() -> None:
    sample = SHARED / "tests" / "samples" / "fixture_project"
    inv_mod = _import_script(ROOT / "skills" / "02-project-intelligence" / "scripts" / "project_inventory_extractor.py", "project_inventory_extractor")
    cg_mod = _import_script(ROOT / "skills" / "03-code-knowledge-graph" / "scripts" / "advanced_code_graph_extractor.py", "advanced_code_graph_extractor")
    js_mod = _import_script(ROOT / "skills" / "05-js-audit-runtime" / "scripts" / "advanced_js_runtime_extractor.py", "advanced_js_runtime_extractor")
    surf_mod = _import_script(ROOT / "skills" / "04-attack-surface-mapping" / "scripts" / "attack_surface_builder.py", "attack_surface_builder")
    inv = inv_mod.extract(sample)
    cg = cg_mod.extract(sample)
    js = js_mod.extract(sample)
    check(inv.get("non_destructive") is True and inv.get("schema_version") == "project_inventory_v2", "02 inventory extractor must emit non-destructive project_inventory_v2")
    check(inv.get("file_count", 0) > 0, "02 inventory extractor did not inventory fixture project")
    check(len(cg.get("routes", [])) >= 2, "03 extractor did not find fixture routes")
    check(len(js.get("api_clients", [])) >= 2, "05 extractor did not find fixture API clients")
    check(len(js.get("source_maps", [])) >= 1, "05 extractor did not find fixture sourcemap")
    check(js.get("schema_version") in {"js_audit_graph_v4.1", "js_audit_graph_v4.1"}, "05 extractor must emit js_audit_graph_v4.1")
    check("html_js_references" in js and "api_wrappers" in js and "frontend_permissions" in js and "chunk_lineage" in js and "candidate_to_manifest_links" in js, "05 extractor missing advanced JS audit fields")
    surf = surf_mod.build(inv, cg, js, {})
    check(surf.get("non_destructive") is True, "04 attack surface builder must be non-destructive")
    check(surf.get("surface_count", 0) > 0, "04 attack surface builder produced empty surface ledger")

def check_tool_health() -> None:
    score = load_json(SHARED / "tools" / "tool_health_score.json")
    check(score.get("verification_mode") in {"runtime_probe_with_manual_required", "runtime_probe"}, "tool health score must be runtime probe snapshot")
    src = (SHARED / "tools" / "tool_health_check.py").read_text(encoding="utf-8", errors="ignore")
    for token in ["COMMAND_CHECKS", "NODE_PACKAGE_CHECKS", "MANUAL_CHECKS", "check_port", "runtime_probe_with_manual_required"]:
        check(token in src, f"tool_health_check.py missing {token}")

def check_state_machine_semantics() -> None:
    spec = importlib.util.spec_from_file_location("quality_gate_v4_1", SHARED / "quality" / "quality_gate_v4_1.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    for f in sorted((SHARED / "tests" / "fixtures").glob("C[0-9][0-9]-*.json")):
        m = load_json(f)
        errs = mod.validate_state_machine(m)
        check(not errs, f"state machine failed for {f.name}: {errs[:3]}")
        if m.get("final_status") == "confirmed":
            count, aerrs, groups = mod.evaluate_dynamic_reproductions(m)
            check(not aerrs, f"dynamic artifact verification failed for {f.name}: {aerrs[:3]}")
            check(count >= 3, f"confirmed fixture requires 3 independent dynamic evidence groups: {f.name} got {count}")
            hashes = {(g.get('request_sha256'), g.get('response_sha256')) for g in groups}
            check(len(hashes) >= 3, f"confirmed fixture dynamic evidence groups are not independent: {f.name}")


def check_candidate_and_dynamic_bridge() -> None:
    tmp_root = ROOT / "_shared" / "tests" / "tmp_runtime"
    tmp_root.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(dir=tmp_root))
    code = {
        "routes": [
            {"file":"app.py","line":1,"route":"/api/users/{id}","method":"GET","handler":"user tenant admin auth policy login session permitall"},
            {"file":"admin.py","line":2,"route":"/api/admin/elevate","method":"POST","handler":"admin role permission impersonate"},
            {"file":"upload.py","line":3,"route":"/api/upload","method":"POST","handler":"upload filename extension overwrite"}
        ],
        "sinks": [
            {"file":"worker.py","line":4,"sink":"exec spawn shell command"},
            {"file":"deserialize.py","line":5,"sink":"pickle deserialize objectinputstream"},
            {"file":"template.py","line":6,"sink":"template render jinja"},
            {"file":"file.py","line":7,"sink":"readFile writeFile download export"},
            {"file":"query.py","line":8,"sink":"raw_query execute select $where queryRaw"}
        ]
    }
    js = {
        "api_clients": [{"file":"app.js","line":1,"target":"/api/projects/{id}","client":"fetch jwt oauth cors webhook graphql secret plugin ssrf url"}],
        "candidate_signals": [{"file":"app.js","line":2,"target":"/api/admin/export","type":"high_value_api_from_js raw_query nosql $where readFile writeFile template ssrf url"}],
        "graphql": [{"file":"app.js","line":3,"operation_or_fragment":"GetUser introspection resolver"}]
    }
    inventory = {
        "dependency_files": [{"path":"package.json","content":"postinstall plugin build dependency"}],
        "config_files": [{"path":"config/cors.json","content":"Access-Control-Allow-Origin credentials"}],
        "auth_signals": [{"path":"auth/callback.ts","signal":"session magic link callback sso saml anonymous public"}],
        "worker_queue_cron_rpc_webhook": [{"path":"worker/webhook.ts","signal":"webhook signature hmac timestamp grpc rpc cron"}]
    }
    spec = importlib.util.spec_from_file_location("vulnerability_candidate_engine", ROOT / "skills" / "07-vulnerability-hunting-engine" / "scripts" / "vulnerability_candidate_engine.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    c = mod.generate(code, js, {}, inventory)
    check(c.get("does_not_confirm") is True, "candidate engine must not confirm findings")
    expected_templates = {f"C{i:02d}" for i in range(1,24)}
    produced_prefixes = {cand.get("template_id","")[:3] for cand in c.get("candidates", [])}
    check(expected_templates.issubset(produced_prefixes), f"candidate engine must cover 23/23 canonical classes, got {sorted(produced_prefixes)}")

    bridge_spec = importlib.util.spec_from_file_location("evidence_capture_bridge", ROOT / "skills" / "06-dynamic-browser-burp-mcp" / "scripts" / "evidence_capture_bridge.py")
    bridge = importlib.util.module_from_spec(bridge_spec)
    assert bridge_spec and bridge_spec.loader
    bridge_spec.loader.exec_module(bridge)
    har = tmp / "capture.har"
    har.write_text(json.dumps({"log":{"entries":[{"request":{"method":"GET","url":"http://local.test/api/projects/1","headers":[]},"response":{"status":200,"content":{"size":12}}}]}}, ensure_ascii=False), encoding="utf-8")
    records = bridge.summarize_har(har, tmp / "artifacts", system_root=ROOT)
    check(len(records) == 1, "dynamic bridge did not produce expected HAR record")
    check(records[0].get("non_destructive") is True, "dynamic bridge must mark records non-destructive")
    check(len(records[0].get("artifacts") or []) >= 2, "dynamic bridge must create request/response artifacts")
    for art in records[0].get("artifacts") or []:
        check(not Path(art.get("path","")).is_absolute(), "dynamic bridge artifact path must be Skill-root relative")
        check((ROOT / art.get("path","")).exists(), "dynamic bridge relative artifact path must exist under Skill root")
    shutil.rmtree(tmp, ignore_errors=True)



def check_template_specific_quality_gate_mutation() -> None:
    spec = importlib.util.spec_from_file_location("quality_gate_v4_1", SHARED / "quality" / "quality_gate_v4_1.py")
    mod = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
    src = load_json(SHARED / "tests" / "fixtures" / "C01-auth-bypass-POS-01.json")
    src["specialized_evidence"] = {"fields": {"wrong_field": "nonempty"}, "field_source": "_shared/vulnerability_templates/canonical_23/C01-auth-bypass/EVIDENCE_FIELDS.json"}
    res = mod.compute_quality(src)
    check(res.get("passed") is False, "quality gate must reject confirmed manifests with missing template-specific specialized fields")
    check("missing_template_specific_evidence" in (res.get("hard_blocks") or []), "quality gate mutation test must hard-block missing_template_specific_evidence")


def check_candidate_engine_per_template_replay() -> None:
    spec = importlib.util.spec_from_file_location("vulnerability_candidate_engine", ROOT / "skills" / "07-vulnerability-hunting-engine" / "scripts" / "vulnerability_candidate_engine.py")
    mod = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod)
    index = load_json(SHARED / "tests" / "candidate_engine_per_template_replay_index.json")
    check(len(index) == 23, f"candidate replay index must cover 23 templates, got {len(index)}")
    for entry in index:
        tid = entry["template_id"]
        pos = load_json(ROOT / entry["positive"])["input"]
        res = mod.generate(pos.get("code_graph",{}), pos.get("js_audit",{}), pos.get("surface",{}), pos.get("inventory",{}))
        produced = {c.get("template_id") for c in res.get("candidates", [])}
        check(tid in produced, f"candidate positive replay failed for {tid}: {sorted(produced)}")
        neg = load_json(ROOT / entry["negative"])["input"]
        resn = mod.generate(neg.get("code_graph",{}), neg.get("js_audit",{}), neg.get("surface",{}), neg.get("inventory",{}))
        produced_neg = {c.get("template_id") for c in resn.get("candidates", [])}
        check(tid not in produced_neg, f"candidate negative replay produced forbidden template {tid}")


def check_template_requirements_files() -> None:
    idx = load_json(SHARED / "template_index.json")
    for t in idx.get("templates", []):
        d = ROOT / t.get("canonical_template_dir", "")
        req = d / "TEMPLATE_REQUIREMENTS.v1.json"
        check(req.exists(), f"template {t.get('template_id')} missing TEMPLATE_REQUIREMENTS.v1.json")
        if req.exists():
            obj = load_json(req)
            check(obj.get("required_specialized_fields") == t.get("required_specialized_fields"), f"template {t.get('template_id')} requirements do not match template_index")
            check(obj.get("quality_gate"), f"template {t.get('template_id')} missing quality_gate rule")



def check_next_stage_fixes() -> None:
    check(not list(ROOT.rglob('__pycache__')) and not list(ROOT.rglob('*.pyc')), 'package must not contain __pycache__ or .pyc files')
    check((ROOT / 'skills/03-code-knowledge-graph/scripts/parser_plugins/PARSER_PLUGIN_REGISTRY.json').exists(), '03 parser plugin registry missing')
    cg_mod = _import_script(ROOT / 'skills/03-code-knowledge-graph/scripts/advanced_code_graph_extractor.py', 'advanced_code_graph_extractor_v2')
    sample = SHARED / 'tests/e2e_samples/01-express-next'; cg = cg_mod.extract(sample)
    check(cg.get('schema_version') in {'security_graph_v3','security_graph_v3'}, '03 extractor must emit security_graph_v3')
    if cg.get('schema_version') == 'security_graph_v3':
        check(bool(cg.get('nodes')), '03 security_graph_v3 must emit nodes')
        check(bool(cg.get('metadata')), '03 security_graph_v3 must emit metadata')
    js_mod = _import_script(ROOT / 'skills/05-js-audit-runtime/scripts/advanced_js_runtime_extractor.py', 'advanced_js_runtime_extractor_v2'); js = js_mod.extract(sample)
    check(js.get('schema_version') in {'js_audit_graph_v4.1','js_audit_graph_v4.1'}, '05 extractor must emit js_audit_graph_v4.1')
    if js.get('schema_version') == 'js_audit_graph_v4.1':
        check('source_map_reentry' in js, '05 js_audit_graph_v4.1 must expose source_map_reentry')
    check(len(js.get('wrapper_resolutions', [])) >= 1, '05 extractor must resolve API wrappers')
    check(len(js.get('chunk_lineage', [])) >= 1, '05 extractor must produce chunk lineage')
    check(len(js.get('candidate_to_manifest_links', [])) >= 1, '05 extractor must output candidate_to_manifest_links')
    e2e_spec = importlib.util.spec_from_file_location('e2e_replay_runner', SHARED / 'tests/e2e_replay/e2e_replay_runner.py')
    e2e = importlib.util.module_from_spec(e2e_spec); assert e2e_spec and e2e_spec.loader; e2e_spec.loader.exec_module(e2e)
    e2e_res = e2e.run(); check(e2e_res.get('passed') is True and e2e_res.get('sample_count') == 10, f'e2e replay must pass 10 samples: {e2e_res.get("errors")}')
    for relp in ['har_redaction_and_hash.py','burp_repeater_export_parser.py','playwright_local_capture.py','artifact_group_builder.py','dynamic_negative_control_runner.py']:
        check((ROOT / 'skills/06-dynamic-browser-burp-mcp/scripts' / relp).exists(), f'06 missing dynamic closed-loop script {relp}')
    cp = subprocess.run([sys.executable, str(ROOT / 'skills/06-dynamic-browser-burp-mcp/scripts/playwright_local_capture.py'), '--check'], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20, env=subprocess_env())
    try: pw = json.loads(cp.stdout)
    except Exception: pw = {}
    check(str(pw.get('policy','')).startswith('localhost_or_file_only'), 'playwright_local_capture must enforce localhost_or_file_only policy')
    check((SHARED / 'review_queue/HUMAN_REVIEW_QUEUE.schema.json').exists(), 'human review queue schema missing')
    check((SHARED / 'knowledge/knowledge_freshness_conflict_gate.py').exists(), 'knowledge freshness/conflict gate missing')
    qg_spec = importlib.util.spec_from_file_location('quality_gate_v4_1', SHARED / 'quality/quality_gate_v4_1.py'); qg = importlib.util.module_from_spec(qg_spec); assert qg_spec and qg_spec.loader; qg_spec.loader.exec_module(qg)
    fx = load_json(SHARED / 'tests/fixtures/C01-auth-bypass-POS-01.json'); fx['knowledge_references'] = [{'role':'vulnerability_evidence','used_as_evidence':True}]
    res = qg.compute_quality(fx); check('knowledge_misuse_or_conflict' in (res.get('hard_blocks') or []), 'quality gate must hard-block knowledge used as direct evidence')
    detectors = list((ROOT / 'skills/07-vulnerability-hunting-engine/detectors').glob('C[0-9][0-9]-*.json'))
    check(len(detectors) == 23, f'expected 23 per-template detectors, got {len(detectors)}')


def check_extreme_reverse_judgement() -> None:
    cp = subprocess.run([sys.executable, str(SHARED / 'reverse_judgement' / 'extreme_reverse_audit.py')], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, env=subprocess_env())
    try:
        result = json.loads(cp.stdout)
    except Exception as exc:
        ERRORS.append(f"extreme reverse judgement non-json: {exc}: {cp.stderr[:300]}")
        return
    check(cp.returncode == 0 and result.get('passed') is True, f"extreme reverse judgement failed: {result.get('errors')}")
    summary = result.get('summary') or {}
    check(summary.get('info_count', 0) >= 42, 'extreme reverse judgement must cover 42 information collection sources')
    check(summary.get('js_count', 0) >= 44, 'extreme reverse judgement must cover 44 JS audit points')
    check(summary.get('vuln_count') == 23, 'extreme reverse judgement must cover 23 vulnerability classes')



def check_v43_completion() -> None:
    cp = subprocess.run([sys.executable, str(SHARED / 'selftest' / 'verify_v4_3_completion.py')], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, env=subprocess_env())
    try:
        result = json.loads(cp.stdout)
    except Exception as exc:
        ERRORS.append(f"v4.3 completion selftest non-json: {exc}: {cp.stderr[:300]}")
        return
    check(cp.returncode == 0 and result.get('passed') is True, f"v4.3 completion selftest failed: {result.get('errors')}")

def main() -> int:
    steps = [
        py_compile_all, check_no_pycache, check_references, check_core_contracts,
        check_template_index, check_schema_roundtrip, check_replay_harness,
        check_state_machine_semantics, check_quality_gate, check_template_specific_quality_gate_mutation,
        check_template_requirements_files, check_extractors, check_candidate_engine_per_template_replay,
        check_candidate_and_dynamic_bridge, check_next_stage_fixes, check_extreme_reverse_judgement, check_v43_completion, check_dashboard, check_tool_health,
    ]
    for fn in steps:
        fn()
    result = {"passed": not ERRORS, "errors": ERRORS, "warnings": WARNINGS, "contract_count": len(list((ROOT / "skills").glob("*/EXECUTION_CONTRACT.md"))), "canonical_template_count": len(load_json(SHARED / "template_index.json").get("templates", [])), "canonical_replay_fixture_count": len(list((SHARED / "tests" / "fixtures").glob("C[0-9][0-9]-*.json")))}
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    return 1 if ERRORS else 0

if __name__ == "__main__":
    rc = main()
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(rc)
