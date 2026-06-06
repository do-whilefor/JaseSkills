import sys
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_c06_c30_high_impact_candidates(tmp_path):
    inp=tmp_path/'in.jsonl'; out=tmp_path/'out.jsonl'
    inp.write_text(json.dumps({'type':'source_sink_candidate','source_file':'app.py','line':3,'endpoint':'/api/fetch?url=','evidence':{'sink_preview':'requests.get(url)'}})+'\n')
    subprocess.run([sys.executable,str(ROOT/'detectors/c06_c30_high_impact_candidates.py'),'--input',str(inp),'-o',str(out)],check=True)
    rows=[json.loads(x) for x in out.read_text().splitlines() if x.strip()]
    assert rows
    assert rows[0]['review_status']=='needs_review'
    assert rows[0]['candidate_vulnerability'].startswith('C')
