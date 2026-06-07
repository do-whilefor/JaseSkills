import sys
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_surface_coverage_audit_reports_40_dimensions(tmp_path):
    hidden=tmp_path/'hidden.jsonl'
    api=tmp_path/'api.jsonl'
    subprocess.run([sys.executable, str(ROOT/'scripts/hidden-info-miner.py'), str(ROOT/'tests/fixtures/hidden_info_app'), '-o', str(hidden)], check=True, timeout=20)
    subprocess.run([sys.executable, str(ROOT/'scripts/api-spec-inventory.py'), str(ROOT/'tests/fixtures/api_spec_app'), '-o', str(api)], check=True, timeout=20)
    out=tmp_path/'coverage.json'
    subprocess.run([sys.executable, str(ROOT/'scripts/surface-coverage-audit.py'), '--root', str(ROOT), '--jsonl', str(hidden), '--jsonl', str(api), '--out', str(out)], check=True, timeout=20)
    data=json.loads(out.read_text())
    assert len(data['results']) == 40
    assert data['summary']['missing'] == 0
    labels={r['dimension']:r['status'] for r in data['results']}
    assert labels['graphql'] == 'implemented'
    assert labels['js_artifacts'] == 'implemented'
