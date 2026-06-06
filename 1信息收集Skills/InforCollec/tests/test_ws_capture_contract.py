import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_ws_readonly_capture_contract(tmp_path):
    out=tmp_path/'ws.json'
    subprocess.run(['node', str(ROOT/'scripts/ws-readonly-capture.mjs'), '--url', 'ws://127.0.0.1:3000/ws', '--out', str(out), '--contract-only'], check=True)
    data=json.loads(out.read_text())
    assert data['schema_version'] == 'ws-readonly-capture.v1'
    assert data['mode'] == 'contract_only'
