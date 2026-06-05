import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_role_matrix_contract_outputs_runtime_evidence(tmp_path):
    outdir=tmp_path/'rm'
    subprocess.run(['node', str(ROOT/'scripts/playwright-har-role-matrix.mjs'), '--config', str(ROOT/'tests/fixtures/role_matrix/config.json'), '--out', str(outdir)], check=True)
    ev=json.loads((outdir/'runtime-evidence.json').read_text())
    assert ev['schema_version'] == 'runtime-evidence.v1'
    assert ev['mode'] == 'contract_only'
    assert len(ev['records']) == 12
    assert all(r['capture_status'] == 'planned_not_captured' for r in ev['records'])
