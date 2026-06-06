import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_api_spec_inventory_extracts_openapi_postman_graphql_grpc(tmp_path):
    out=tmp_path/'api.jsonl'
    subprocess.run(['python3', str(ROOT/'scripts/api-spec-inventory.py'), str(ROOT/'tests/fixtures/api_spec_app'), '-o', str(out)], check=True)
    rows=[json.loads(x) for x in out.read_text().splitlines() if x.strip()]
    types={r['type'] for r in rows}
    assert 'openapi_path_operation' in types
    assert 'postman_request' in types
    assert 'graphql_operation' in types
    assert 'graphql_schema_type' in types
    assert 'grpc_rpc_method' in types
    assert any(r.get('endpoint')=='/api/admin/users' for r in rows)
    assert all(r['dynamic_status']=='not_validated' for r in rows)

def test_api_spec_inventory_dry_run():
    proc=subprocess.run(['python3', str(ROOT/'scripts/api-spec-inventory.py'), str(ROOT/'tests/fixtures/api_spec_app'), '--dry-run'], text=True, capture_output=True, check=True)
    data=json.loads(proc.stdout)
    assert data['network']=='disabled'
