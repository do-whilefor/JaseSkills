# 22 JS Framework and Schema Deep Parser

## Trigger
Use when JS audit needs AST wrapper resolution, sourcemap reconstruction, framework build artifact parsing, schema alignment, service worker cache review, CDN history candidate enumeration, or hidden feature signal extraction.

## Execution
Run these scripts in order after collection/analyze:

- `scripts/js_wrapper_resolver.py`
- `scripts/js_sourcemap_reconstructor.py`
- `scripts/js_framework_build_parser.py`
- `scripts/js_schema_alignment.py`
- `scripts/js_service_worker_cache_auditor.py`
- `scripts/js_cdn_history_asset_enumerator.py`
- `scripts/js_hidden_feature_extractor.py`
- `scripts/js_business_flow_template_generator.py`

## Evidence standard
All outputs are candidate-only until cross-linked with AST, HAR, browser replay, backend acceptance, and role/tenant evidence. Schema-only fields are hidden parameter candidates, not backend-accepted parameters.
