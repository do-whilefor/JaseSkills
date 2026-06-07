import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def load_module():
    path = ROOT/'scripts/source-sink-dataflow.py'
    spec = importlib.util.spec_from_file_location('source_sink_dataflow', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

def test_source_sink_dataflow_flags_file_and_command_candidates():
    mod = load_module()
    app = ROOT/'tests/fixtures/dataflow_app'
    rows=[]
    for path in mod.walk(app):
        rows.extend(mod.scan_file(path, app))
    vulns={r['candidate_vulnerability'] for r in rows}
    assert 'arbitrary_file_access_candidate' in vulns
    assert 'command_injection_candidate' in vulns
    assert all(r['review_status'] == 'needs_review' for r in rows)
