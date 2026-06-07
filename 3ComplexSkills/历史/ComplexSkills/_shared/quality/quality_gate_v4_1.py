#!/usr/bin/env python3
"""Executable Quality Gate v4.1 for authorized local security audit evidence manifests.

Extreme P0 repair:
- Recomputes three independent non-destructive reproduction groups from artifacts.
- Verifies every artifact path is Skill-root relative and sha256 matches disk.
- Reads _shared/template_index.json and enforces template-specific required fields.
- Treats candidate engine output and tool alerts as candidate-only, never confirmed.
- Fails closed on out-of-scope, destructive validation, missing code evidence,
  missing negative control, missing specialized evidence, or prompt-injection taint.
"""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "_shared" / "evidence" / "EVIDENCE_MANIFEST_SCHEMA.v4.1.json"
CONFIG_PATH = Path(__file__).with_name("quality_gate_v4_1.yaml")
STATE_MACHINE_PATH = ROOT / "_shared" / "state_machine" / "candidate_state_machine.json"
TEMPLATE_INDEX_PATH = ROOT / "_shared" / "template_index.json"

try:
    import yaml  # type: ignore
except Exception:
    yaml = None
try:
    import jsonschema  # type: ignore
except Exception:
    jsonschema = None

PROMPT_INJECTION_MARKERS = [
    "ignore previous instructions", "忽略之前", "system prompt", "developer message",
    "you are now", "disregard", "override rules", "越权", "不要遵守"
]

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def load_config() -> dict[str, Any]:
    if yaml is None:
        return {"thresholds": {"confirmed_minimum_score": 85, "confirmed_minimum_reproduction_count": 3}, "scoring": {}}
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

def template_map() -> dict[str, Any]:
    idx = load_json(TEMPLATE_INDEX_PATH)
    return {t.get("template_id"): t for t in idx.get("templates", []) if t.get("template_id")}

def schema_errors(manifest: dict[str, Any], schema_path: Path = SCHEMA_PATH) -> list[str]:
    if jsonschema is None:
        return ["jsonschema package is required for true JSON Schema validation"]
    schema = load_json(schema_path)
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{'.'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in sorted(validator.iter_errors(manifest), key=lambda e: list(e.absolute_path))]

def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()

def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8', 'ignore')).hexdigest()

def re_full_sha(value: str) -> bool:
    return len(value) == 64 and all(c in '0123456789abcdefABCDEF' for c in value)

def validate_state_machine(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        sm = load_json(STATE_MACHINE_PATH)
    except Exception as exc:
        return [f"state machine load failed: {exc}"]
    states = set(sm.get('states') or [])
    transitions = sm.get('transitions') or {}
    forbidden = {(x.get('from'), x.get('to')) for x in sm.get('forbidden_transitions') or []}
    hist = manifest.get('state_history') or []
    if not isinstance(hist, list) or not hist:
        return ["state_history missing or empty"]
    prev_to = None
    for i, step in enumerate(hist):
        if not isinstance(step, dict):
            errors.append(f"state_history[{i}] is not an object"); continue
        fr = step.get('from_state')
        to = step.get('to_state')
        if to not in states:
            errors.append(f"state_history[{i}] to_state not in state machine: {to}")
        if i == 0:
            if fr is not None or to != 'discovered':
                errors.append("state_history must start with null -> discovered")
        else:
            if fr != prev_to:
                errors.append(f"state_history[{i}] from_state {fr} does not match previous to_state {prev_to}")
            if (fr, to) in forbidden or to not in transitions.get(fr, []):
                errors.append(f"forbidden state transition: {fr} -> {to}")
        prev_to = to
    state = manifest.get('state')
    final_status = manifest.get('final_status')
    expected_state = {"confirmed":"confirmed", "rejected":"rejected", "blocked":"validation_blocked", "needs_human_review":"needs_human_review", "candidate":"triaged"}.get(final_status)
    if expected_state and state != expected_state:
        errors.append(f"state {state} does not match final_status {final_status}; expected {expected_state}")
    if prev_to and state != prev_to:
        errors.append(f"state {state} does not match last state_history transition {prev_to}")
    if final_status == 'confirmed':
        required = ['discovered','mapped','triaged','validation_planned','reproduced','negative_control_passed','quality_gate_passed','confirmed']
        got = [x.get('to_state') for x in hist if isinstance(x, dict)]
        pos = -1
        for req in required:
            try:
                pos = got.index(req, pos + 1)
            except ValueError:
                errors.append(f"confirmed candidate missing required state: {req}")
                break
    return errors

def artifact_path_under_root(rel: str) -> Path:
    ap = (ROOT / rel).resolve()
    ap.relative_to(ROOT)
    return ap

def evaluate_dynamic_reproductions(manifest: dict[str, Any]) -> tuple[int, list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    verified: list[dict[str, Any]] = []
    dyn = manifest.get('dynamic_evidence') or []
    if not isinstance(dyn, list):
        return 0, ["dynamic_evidence is not an array"], []
    seen_case_ids: set[str] = set()
    seen_hash_pairs: set[tuple[str, str]] = set()
    for i, entry in enumerate(dyn):
        prefix = f"dynamic_evidence[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} is not an object"); continue
        case_id = entry.get('case_id')
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{prefix} missing case_id"); continue
        if case_id in seen_case_ids:
            errors.append(f"{prefix} duplicate case_id: {case_id}"); continue
        seen_case_ids.add(case_id)
        if entry.get('non_destructive') is not True:
            errors.append(f"{prefix} must be non_destructive=true"); continue
        arts = entry.get('artifacts')
        if not isinstance(arts, list) or not arts:
            errors.append(f"{prefix} missing artifacts"); continue
        by_type: dict[str, list[str]] = {'request': [], 'response': []}
        group_errors: list[str] = []
        for j, art in enumerate(arts):
            art_prefix = f"{prefix}.artifacts[{j}]"
            if not isinstance(art, dict):
                group_errors.append(f"{art_prefix} is not an object"); continue
            typ = art.get('type'); rel = art.get('path'); want = art.get('sha256')
            if art.get('redacted') is not True:
                group_errors.append(f"{art_prefix} must be redacted=true")
            if not isinstance(rel, str) or not rel:
                group_errors.append(f"{art_prefix} missing path"); continue
            if Path(rel).is_absolute():
                group_errors.append(f"{art_prefix} path must be relative to Skill root: {rel}"); continue
            try:
                ap = artifact_path_under_root(rel)
            except Exception:
                group_errors.append(f"{art_prefix} path escapes system root: {rel}"); continue
            if not ap.exists() or not ap.is_file():
                group_errors.append(f"{art_prefix} file missing: {rel}"); continue
            if not isinstance(want, str) or not re_full_sha(want):
                group_errors.append(f"{art_prefix} missing valid sha256"); continue
            got = sha_file(ap)
            if got.lower() != want.lower():
                group_errors.append(f"{art_prefix} sha256 mismatch for {rel}"); continue
            if typ in by_type:
                by_type[typ].append(got.lower())
        if group_errors:
            errors.extend(group_errors[:8]); continue
        if not by_type['request'] or not by_type['response']:
            errors.append(f"{prefix} requires at least one request and one response artifact"); continue
        pair = (by_type['request'][0], by_type['response'][0])
        if pair in seen_hash_pairs:
            errors.append(f"{prefix} duplicates request/response artifact hash pair; not independent"); continue
        seen_hash_pairs.add(pair)
        verified.append({'case_id': case_id, 'request_sha256': pair[0], 'response_sha256': pair[1], 'artifact_count': len(arts)})
    return len(verified), errors, verified

def validate_template_specific_evidence(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    tid = manifest.get('template_id')
    tmap = template_map()
    tpl = tmap.get(tid)
    if not tpl:
        return False, [f"template_id not indexed: {tid}"]
    required = tpl.get('required_specialized_fields') or []
    spec = manifest.get('specialized_evidence') or {}
    fields = spec.get('fields') if isinstance(spec, dict) else None
    if not isinstance(fields, dict):
        return False, ["specialized_evidence.fields missing or not object"]
    for name in required:
        v = fields.get(name)
        if v is None or v == "" or v == [] or v == {}:
            errors.append(f"missing template-specific evidence field: {name}")
    fs = spec.get('field_source') if isinstance(spec, dict) else None
    expected_fs = tpl.get('evidence_fields')
    if expected_fs and fs != expected_fs:
        errors.append(f"specialized_evidence.field_source mismatch: expected {expected_fs}, got {fs}")
    if expected_fs and not (ROOT / expected_fs).exists():
        errors.append(f"template evidence_fields file missing: {expected_fs}")
    rt = manifest.get('report_template')
    expected_rt = tpl.get('report_template')
    if expected_rt and rt != expected_rt:
        errors.append(f"report_template mismatch: expected {expected_rt}, got {rt}")
    if expected_rt and not (ROOT / expected_rt).exists():
        errors.append(f"report_template file missing: {expected_rt}")
    return not errors, errors

def detect_prompt_injection_taint(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    trusted = manifest.get('extractor_trace', {}) if isinstance(manifest.get('extractor_trace'), dict) else {}
    text_fields = []
    for key in ['false_positive_notes', 'source_file', 'route', 'parameter', 'request_summary', 'response_summary']:
        if isinstance(manifest.get(key), str):
            text_fields.append((key, manifest[key]))
    for section in manifest.get('report_sections') or []:
        if isinstance(section, str): text_fields.append(('report_sections', section))
    for key, val in text_fields:
        low = val.lower()
        if any(marker in low for marker in PROMPT_INJECTION_MARKERS):
            if trusted.get('prompt_injection_reviewed') is not True:
                errors.append(f"prompt injection marker in {key} without extractor_trace.prompt_injection_reviewed=true")
    for container_key in ['code_evidence','dynamic_evidence','negative_control','report_sections']:
        val = manifest.get(container_key)
        blob = json.dumps(val, ensure_ascii=False).lower() if val is not None else ''
        if any(marker in blob for marker in PROMPT_INJECTION_MARKERS):
            tr = manifest.get('taint_review') if isinstance(manifest.get('taint_review'), dict) else {}
            if tr.get('decision') not in {'reviewed_safe','clean'}:
                errors.append(f'prompt injection marker in {container_key} without taint_review decision clean/reviewed_safe')
    tr = manifest.get('taint_review') if isinstance(manifest.get('taint_review'), dict) else {}
    if manifest.get('final_status') == 'confirmed':
        required_sources = {'README','source_comments','sourcemap','HAR','fixture','report_sections'}
        reviewed = set(tr.get('untrusted_sources_reviewed') or [])
        missing = sorted(required_sources - reviewed)
        if missing:
            errors.append(f'taint_review missing untrusted sources: {missing}')
        if tr.get('decision') not in {'clean','reviewed_safe'}:
            errors.append('confirmed requires taint_review.decision clean or reviewed_safe')
    return errors



def validate_evidence_id_and_claims(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    """Confirmed findings must have first-class evidence IDs and report claims bound to them."""
    errors: list[str] = []
    if manifest.get('final_status') != 'confirmed':
        return True, []
    evid = manifest.get('evidence_id')
    if not isinstance(evid, str) or not evid.startswith('EVID-'):
        errors.append('confirmed requires evidence_id starting with EVID-')
    if not manifest.get('manifest_id'):
        errors.append('confirmed requires manifest_id')
    claims = manifest.get('report_claims')
    if not isinstance(claims, list) or not claims:
        errors.append('confirmed requires non-empty report_claims')
    else:
        for i, c in enumerate(claims):
            if not isinstance(c, dict):
                errors.append(f'report_claims[{i}] is not an object'); continue
            if c.get('evidence_id') != evid:
                errors.append(f'report_claims[{i}].evidence_id must equal manifest evidence_id')
            if c.get('level') != 'confirmed':
                errors.append(f'report_claims[{i}].level must be confirmed for confirmed manifest')
            if not c.get('claim_id') or not c.get('text'):
                errors.append(f'report_claims[{i}] missing claim_id/text')
    return not errors, errors


def validate_redaction_and_command_outputs(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    """Block hand-written confirmed manifests that lack executed/redacted command-output artifacts.

    This does not provide cryptographic non-repudiation, but it prevents a bare JSON file
    from passing as confirmed evidence. Each command output must point to a real local
    redacted stdout/stderr artifact whose hashes match the manifest.
    """
    errors: list[str] = []
    if manifest.get('final_status') != 'confirmed':
        return True, []
    red = manifest.get('redaction') if isinstance(manifest.get('redaction'), dict) else {}
    if red.get('secrets_scanned') is not True or red.get('second_pass_complete') is not True:
        errors.append('confirmed requires redaction.secrets_scanned=true and second_pass_complete=true')
    command_outputs = manifest.get('command_outputs')
    if not isinstance(command_outputs, list) or not command_outputs:
        return False, errors + ['confirmed requires command_outputs attestation entries']
    for i, co in enumerate(command_outputs):
        prefix=f'command_outputs[{i}]'
        if not isinstance(co, dict):
            errors.append(f'{prefix} is not an object'); continue
        for key in ['command_id','command','exit_code','stdout_sha256','stderr_sha256','artifact_path','redacted']:
            if key not in co:
                errors.append(f'{prefix} missing {key}')
        if co.get('redacted') is not True:
            errors.append(f'{prefix}.redacted must be true')
        if not isinstance(co.get('command'), list) or not co.get('command'):
            errors.append(f'{prefix}.command must be non-empty array')
        rel=co.get('artifact_path')
        if not isinstance(rel, str) or not rel:
            continue
        ap=Path(rel)
        if ap.is_absolute():
            try:
                ap=ap.resolve(); ap.relative_to(ROOT)
            except Exception:
                errors.append(f'{prefix}.artifact_path must be relative to Skill root or inside it: {rel}'); continue
        else:
            ap=(ROOT/rel).resolve()
            try: ap.relative_to(ROOT)
            except Exception:
                errors.append(f'{prefix}.artifact_path escapes Skill root: {rel}'); continue
        if not ap.exists() or not ap.is_file():
            errors.append(f'{prefix}.artifact file missing: {rel}'); continue
        try:
            payload=json.loads(ap.read_text(encoding='utf-8', errors='ignore'))
        except Exception as exc:
            errors.append(f'{prefix}.artifact non-json: {exc.__class__.__name__}'); continue
        stdout=str(payload.get('stdout',''))
        stderr=str(payload.get('stderr',''))
        if sha_text(stdout).lower()!=str(co.get('stdout_sha256','')).lower():
            errors.append(f'{prefix}.stdout_sha256 mismatch')
        if sha_text(stderr).lower()!=str(co.get('stderr_sha256','')).lower():
            errors.append(f'{prefix}.stderr_sha256 mismatch')
    return not errors, errors


def validate_static_source_paths(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if manifest.get('final_status') != 'confirmed':
        return True, []
    paths=[]
    if isinstance(manifest.get('source_file'), str):
        paths.append(('source_file', manifest.get('source_file')))
    for i, ev in enumerate(manifest.get('code_evidence') or []):
        if isinstance(ev, dict) and isinstance(ev.get('file'), str):
            paths.append((f'code_evidence[{i}].file', ev.get('file')))
    for name, rel in paths:
        if not rel:
            errors.append(f'{name} empty'); continue
        p=Path(rel)
        if p.is_absolute():
            try:
                p=p.resolve(); p.relative_to(ROOT)
            except Exception:
                errors.append(f'{name} must be relative to Skill root or inside it: {rel}'); continue
        else:
            p=(ROOT/rel).resolve()
            try: p.relative_to(ROOT)
            except Exception:
                errors.append(f'{name} escapes Skill root: {rel}'); continue
        if not p.exists() or not p.is_file():
            errors.append(f'{name} file missing: {rel}')
    return not errors, errors


def validate_role_object_tenant_ledger(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    tid = manifest.get('template_id')
    if tid not in {'C03-idor-bola','C04-tenant-isolation-bypass'} or manifest.get('final_status') != 'confirmed':
        return True, []
    ledger = manifest.get('role_object_tenant_ledger')
    spec_fields = ((manifest.get('specialized_evidence') or {}).get('fields') or {})
    if ledger is None and spec_fields.get('role_object_tenant_ledger'):
        ledger = spec_fields.get('role_object_tenant_ledger')
    errors=[]
    if not isinstance(ledger, dict):
        return False, ['C03/C04 confirmed findings require role_object_tenant_ledger object']
    if ledger.get('complete') is not True:
        errors.append('role_object_tenant_ledger.complete must be true')
    if int(ledger.get('unresolved_count') or 0) != 0:
        errors.append('role_object_tenant_ledger.unresolved_count must be 0 for confirmed C03/C04')
    if ledger.get('high_risk_unresolved_routes'):
        errors.append('role_object_tenant_ledger.high_risk_unresolved_routes must be empty')
    if not ledger.get('object_bindings'):
        errors.append('role_object_tenant_ledger.object_bindings required')
    if tid == 'C04-tenant-isolation-bypass' and not ledger.get('tenant_bindings'):
        errors.append('C04 requires tenant_bindings in role_object_tenant_ledger')
    if not ledger.get('negative_control_coverage'):
        errors.append('role_object_tenant_ledger.negative_control_coverage required')
    return not errors, errors


def validate_report_renderer(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    rr = manifest.get('report_renderer')
    tid = manifest.get('template_id')
    errors=[]
    if manifest.get('final_status') == 'confirmed':
        if not isinstance(rr, dict):
            return False, ['confirmed report requires report_renderer object']
        if rr.get('template_id') != tid:
            errors.append('report_renderer.template_id must match manifest.template_id')
        if rr.get('generic_renderer_forbidden') is not True:
            errors.append('report_renderer.generic_renderer_forbidden must be true')
        if rr.get('quality_gate_checked') is not True:
            errors.append('report_renderer.quality_gate_checked must be true')
        rp = rr.get('renderer_path')
        if rp and not (ROOT / rp).exists():
            errors.append(f'report renderer path missing: {rp}')
    return not errors, errors


def validate_knowledge_references(manifest: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    refs = manifest.get('knowledge_references') or []
    if not isinstance(refs, list):
        return False, ['knowledge_references must be an array when present']
    for i, ref in enumerate(refs):
        if not isinstance(ref, dict):
            errors.append(f'knowledge_references[{i}] is not an object'); continue
        if ref.get('used_as_evidence') is True or ref.get('role') in {'vulnerability_evidence','code_evidence','dynamic_evidence'}:
            errors.append(f'knowledge_references[{i}] cannot be direct vulnerability evidence')
        if ref.get('conflict') is True and manifest.get('final_status') == 'confirmed':
            errors.append(f'knowledge_references[{i}] conflict cannot be confirmed')
        if ref.get('stale') is True and ref.get('freshness_reviewed') is not True:
            errors.append(f'knowledge_references[{i}] stale without freshness_reviewed=true')
    return not errors, errors

def compute_quality(manifest: dict[str, Any], schema_path: Path = SCHEMA_PATH) -> dict[str, Any]:
    config = load_config()
    scoring = config.get('scoring', {})
    thresholds = config.get('thresholds', {})
    min_score = int(thresholds.get('confirmed_minimum_score', 85))
    min_repro = int(thresholds.get('confirmed_minimum_reproduction_count', 3))
    errors = schema_errors(manifest, schema_path)
    state_errors = validate_state_machine(manifest)
    independent_repro_count, dyn_artifact_errors, verified_reproductions = evaluate_dynamic_reproductions(manifest)
    template_ok, template_errors = validate_template_specific_evidence(manifest)
    prompt_errors = detect_prompt_injection_taint(manifest)
    knowledge_ok, knowledge_errors = validate_knowledge_references(manifest)
    ledger_ok, ledger_errors = validate_role_object_tenant_ledger(manifest)
    evidence_id_ok, evidence_id_errors = validate_evidence_id_and_claims(manifest)
    command_ok, command_errors = validate_redaction_and_command_outputs(manifest)
    source_paths_ok, source_path_errors = validate_static_source_paths(manifest)
    renderer_ok, renderer_errors = validate_report_renderer(manifest)
    reasons: list[str] = []
    hard_blocks: list[str] = []
    checks: dict[str, bool] = {}
    total = 0
    def add(name: str, ok: bool, reason: str) -> None:
        nonlocal total
        checks[name] = bool(ok)
        if ok:
            total += int(scoring.get(name, 0))
        else:
            reasons.append(reason)

    add('schema_valid', not errors, 'schema validation failed')
    if errors: reasons.extend(errors[:10])
    checks['state_machine_valid'] = not state_errors
    if state_errors:
        hard_blocks.append('invalid_state_transition'); reasons.extend(state_errors[:10])
    checks['artifact_hashes_valid'] = not dyn_artifact_errors
    checks['independent_reproduction_groups'] = independent_repro_count >= min_repro
    checks['template_specific_evidence_valid'] = template_ok
    if template_errors: reasons.extend(template_errors[:10])
    checks['prompt_injection_reviewed'] = not prompt_errors
    checks['knowledge_freshness_conflict_valid'] = knowledge_ok
    if knowledge_errors:
        hard_blocks.append('knowledge_misuse_or_conflict'); reasons.extend(knowledge_errors[:10])
    checks['role_object_tenant_ledger_valid'] = ledger_ok
    if ledger_errors:
        hard_blocks.append('role_object_tenant_ledger_incomplete'); reasons.extend(ledger_errors[:10])
    checks['template_specific_report_renderer_valid'] = renderer_ok
    if renderer_errors:
        hard_blocks.append('generic_or_missing_report_renderer'); reasons.extend(renderer_errors[:10])
    checks['evidence_id_and_report_claims_valid'] = evidence_id_ok
    if evidence_id_errors:
        hard_blocks.append('missing_or_invalid_evidence_id_or_report_claims'); reasons.extend(evidence_id_errors[:10])
    checks['command_output_attestations_valid'] = command_ok
    if command_errors:
        hard_blocks.append('missing_or_invalid_command_output_attestation'); reasons.extend(command_errors[:10])
    checks['static_source_paths_valid'] = source_paths_ok
    if source_path_errors:
        hard_blocks.append('missing_or_invalid_static_source_path'); reasons.extend(source_path_errors[:10])
    if prompt_errors:
        hard_blocks.append('prompt_injection_taint'); reasons.extend(prompt_errors[:10])

    auth_scope = manifest.get('authorization_scope')
    if auth_scope not in {'local_authorized_fixture_only', 'local_authorized_project_only'}:
        hard_blocks.append('out_of_scope')
    final_status = manifest.get('final_status')
    if final_status == 'confirmed':
        if dyn_artifact_errors:
            hard_blocks.append('missing_or_invalid_dynamic_artifacts'); reasons.extend(dyn_artifact_errors[:10])
        if independent_repro_count < min_repro:
            hard_blocks.append('insufficient_independent_reproduction_groups')
            reasons.append(f"confirmed requires {min_repro} independent dynamic reproduction groups, got {independent_repro_count}")
        if not template_ok:
            hard_blocks.append('missing_template_specific_evidence')
        if prompt_errors:
            hard_blocks.append('prompt_injection_taint')

    code = manifest.get('code_evidence') or []
    add('code_evidence', isinstance(code, list) and len(code) > 0, 'missing code evidence')
    if final_status == 'confirmed' and not code:
        hard_blocks.append('missing_code_evidence_for_confirmed')

    route_ok = bool(manifest.get('route') and manifest.get('method'))
    add('route_parameter_mapping', route_ok, 'missing route/method mapping')
    ctx_ok = bool(manifest.get('auth_context') and manifest.get('tenant_context'))
    add('auth_role_tenant_context', ctx_ok, 'missing auth or tenant context')
    dyn = manifest.get('dynamic_evidence') or []
    dyn_ok = isinstance(dyn, list) and len(dyn) > 0 and not dyn_artifact_errors
    add('dynamic_request_response', dyn_ok, 'missing or invalid dynamic evidence')
    neg = manifest.get('negative_control') or []
    neg_ok = isinstance(neg, list) and len(neg) > 0
    add('negative_control', neg_ok, 'missing negative controls')
    if final_status == 'confirmed' and not neg_ok:
        hard_blocks.append('missing_negative_control_for_confirmed')
    add('reproduction_stability', independent_repro_count >= min_repro, 'insufficient independent reproduction groups')
    impact = manifest.get('impact') or {}
    impact_ok = isinstance(impact, dict) and bool(impact.get('impact_type') or impact.get('impact_summary') or impact.get('security_impact') or impact.get('affected_asset'))
    add('security_impact', impact_ok, 'missing impact proof')
    boundary = manifest.get('non_destructive_boundary') or {}
    nd_ok = isinstance(boundary, dict) and (boundary.get('non_destructive') is True or str(boundary.get('validation_mode','')).startswith('local_') or 'read-only local fixture replay' in (boundary.get('allowed') or []))
    add('non_destructive_boundary', nd_ok, 'missing non-destructive boundary')
    if final_status == 'confirmed' and not nd_ok:
        hard_blocks.append('destructive_validation')
    fp_ok = bool(manifest.get('false_positive_notes'))
    add('false_positive_filter', fp_ok, 'missing false-positive notes')
    add('specialized_evidence', template_ok, 'missing template-specific evidence')
    report_ok = bool(manifest.get('report_template') and manifest.get('report_sections'))
    add('report_traceability', report_ok, 'missing report traceability')
    if final_status == 'confirmed' and not manifest.get('tool_snapshot'):
        hard_blocks.append('missing_tool_snapshot_for_confirmed')
    if final_status == 'confirmed' and manifest.get('fixture_type') in {'tool_alert_only', 'candidate_only'}:
        hard_blocks.append('candidate_or_tool_alert_cannot_confirm')

    passed = final_status == 'confirmed' and total >= min_score and not hard_blocks and all([
        checks.get('schema_valid'), checks.get('state_machine_valid'), checks.get('artifact_hashes_valid'),
        checks.get('independent_reproduction_groups'), checks.get('template_specific_evidence_valid'),
        checks.get('code_evidence'), checks.get('dynamic_request_response'), checks.get('negative_control'),
        checks.get('security_impact'), checks.get('non_destructive_boundary'), checks.get('false_positive_filter'),
        checks.get('report_traceability'), checks.get('role_object_tenant_ledger_valid', True), checks.get('template_specific_report_renderer_valid', True),
        checks.get('evidence_id_and_report_claims_valid'), checks.get('command_output_attestations_valid'), checks.get('static_source_paths_valid')
    ])
    return {
        'schema_version': 'quality_gate_result_v4.1', 'schema_valid': checks.get('schema_valid', False),
        'status_valid': not hard_blocks, 'passed': bool(passed), 'total': total, 'threshold': min_score,
        'checks': checks, 'hard_blocks': sorted(set(hard_blocks)), 'reasons': reasons[:50],
        'independent_reproduction_count': independent_repro_count, 'verified_reproductions': verified_reproductions,
        'template_specific_required_fields': (template_map().get(manifest.get('template_id')) or {}).get('required_specialized_fields', [])
    }

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest')
    ap.add_argument('--schema', default=str(SCHEMA_PATH))
    args = ap.parse_args()
    manifest = load_json(Path(args.manifest))
    result = compute_quality(manifest, Path(args.schema))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get('passed') else 1
if __name__ == '__main__':
    raise SystemExit(main())
