import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_js_ast_endpoint_extractor_outputs_endpoint_candidates(tmp_path):
    out = tmp_path / 'js_ast.jsonl'
    subprocess.run(['node', str(ROOT/'scripts/js-ast-endpoint-extractor.mjs'), str(ROOT/'tests/fixtures/js_ast_app'), '-o', str(out)], check=True)
    rows = [json.loads(x) for x in out.read_text().splitlines() if x.strip()]
    assert rows
    assert any('/api/admin/users/' in r.get('endpoint','') for r in rows)
    assert any(r.get('sink_type') == 'websocket' for r in rows)
    assert all(r.get('review_status') == 'needs_review' for r in rows)
