# Quality Gate v4.1.1

This gate is executable. The source of truth is `_shared/quality/quality_gate_v4_1.py` and `_shared/quality/quality_gate_v4_1.yaml`.

A vulnerability may be marked `confirmed` only when all of the following are true:

1. The evidence manifest validates against `_shared/evidence/EVIDENCE_MANIFEST_SCHEMA.v4.1.json` with `jsonschema` Draft 2020-12.
2. The quality score is at least 85.
3. `reproduction_count >= 3`.
4. Code evidence, dynamic evidence, negative control, false-positive notes, auth/tenant context, specialized evidence fields and report sections are present.
5. Every dynamic validation evidence item is marked `non_destructive: true`.
6. The target scope is `local_authorized_fixture_only` or `local_authorized_project_only`.
7. Tool output is treated as candidate support only; it cannot confirm a vulnerability without code and dynamic evidence.

Blocked, rejected and needs-human-review statuses are explicit states and must not be converted into confirmed findings by template routing alone.
