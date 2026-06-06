import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_qg_jsonl_score_passes_candidate_and_fails_bad_confirmed(tmp_path):
    out=tmp_path/'score.json'
    subprocess.run(['python3', str(ROOT/'scripts/qg-jsonl-score.py'), '--input', str(ROOT/'tests/fixtures/qg/candidate.jsonl'), '--input', str(ROOT/'tests/fixtures/qg/bad_confirmed.jsonl'), '-o', str(out)], check=True)
    s=json.loads(out.read_text())
    assert s['total'] == 2
    assert s['failed'] == 1
    assert any('confirmed_missing_request_sample' in rec['errors'] for rec in s['records'])
