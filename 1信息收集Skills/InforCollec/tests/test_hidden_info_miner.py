import sys
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def run_hidden(tmp_path):
    out=tmp_path/'hidden.jsonl'
    subprocess.run([sys.executable, str(ROOT/'scripts/hidden-info-miner.py'), str(ROOT/'tests/fixtures/hidden_info_app'), '-o', str(out)], check=True)
    return [json.loads(x) for x in out.read_text().splitlines() if x.strip()]

def test_hidden_info_miner_detects_deep_hidden_surfaces(tmp_path):
    rows=run_hidden(tmp_path)
    types={r['type'] for r in rows}
    expected={'comment_hidden_security_hint','source_map_reference','source_map_original_source','source_map_endpoint_literal','graphql_operation_name','websocket_event_name','feature_flag_or_experiment','service_worker_cache_or_route_hint','manifest_path_or_asset','cicd_deployment_or_secret_name_hint','container_iac_internal_service_hint','cloud_or_third_party_service_hint','test_seed_default_account_or_role','package_script_hidden_command','reverse_proxy_hidden_path','well_known_public_path_file','domain_or_callback_url_hint'}
    assert expected <= types

def test_hidden_info_miner_redacts_secret_values(tmp_path):
    rows=run_hidden(tmp_path)
    blob='\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)
    assert 'ChangeMe123' not in blob
    assert 'PROD_API_TOKEN: ${{ secrets.PROD_API_TOKEN }}' not in blob or '****' in blob

def test_hidden_info_miner_dry_run(tmp_path):
    proc=subprocess.run([sys.executable, str(ROOT/'scripts/hidden-info-miner.py'), str(ROOT/'tests/fixtures/hidden_info_app'), '--dry-run'], text=True, capture_output=True, check=True)
    data=json.loads(proc.stdout)
    assert data['network']=='disabled'
    assert data['files_to_scan'] > 0
