# Changelog

## 3.1-clean - 2026-06-06

### Preserved

- Kept `_shared/knowledge/` unchanged from the original package.
- Kept the original `_shared/vulnerability_templates/` files unchanged from the original package.
- Kept the v3 semantic graph builder, framework extractors, candidate-to-replay planner, evidence importers, adversarial harness, dashboard drill-down, severe vulnerability fixtures, and final claim guard.

### Cleaned

- Moved executable template overlays out of `_shared/vulnerability_templates/` into `_shared/executable_template_overlays/` so the original vulnerability template tree remains clean.
- Removed transient replay result snapshots and superseded v3 repair-summary files from the installable release.
- Removed cache/trash file classes such as `__pycache__`, `.pyc`, `.tmp`, `.bak`, `.log`, `.DS_Store` when present.

### Updated

- Added versioned release metadata under `_shared/release/`.
- Added root `VERSION.md`, `CHANGELOG.md`, and `PACKAGE_CLEANUP_REPORT.md`.
- Updated install and verification instructions to use the actual package root name `My-Skills-End`.
