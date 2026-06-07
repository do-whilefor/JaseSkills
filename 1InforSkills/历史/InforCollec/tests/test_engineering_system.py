from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'engineering_system'


def run(cmd, timeout=90):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)


@pytest.fixture(scope='module')
def pipeline_out(tmp_path_factory):
    out = tmp_path_factory.mktemp('info_end_run')
    proc = run([sys.executable, 'info_end_run.py', '--input', str(FIXTURE), '--scope', str(FIXTURE), '--output', str(out), '--max-files', '200'], timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return out


def test_required_engineering_directories_exist():
    for directory in ['collectors','analyzers','schemas','reports','quality']:
        assert (ROOT / directory).is_dir()
    for collector in ['route_collector','js_asset_collector','config_collector','dependency_collector','docs_collector','ci_cd_collector','iac_collector','graphql_collector','websocket_collector','sourcemap_collector','hidden_parameter_collector']:
        assert (ROOT / 'collectors' / f'{collector}.py').exists()


def test_collectors_manifest_quality_pipeline(pipeline_out):
    manifest = pipeline_out / 'evidence-manifest.json'
    quality = pipeline_out / 'unified-quality-gate.json'
    assert manifest.exists()
    assert quality.exists()
    m = json.loads(manifest.read_text())
    q = json.loads(quality.read_text())
    types = {x.get('discovered_item_type') for x in m['items']}
    assert 'endpoint' in types
    assert 'source_map_artifact' in types
    assert 'secret_name_signal' in types
    assert 'dangerous_package_script' in types
    assert q['status'] == 'PASS'


def test_redaction_gate_blocks_unredacted_secret(tmp_path):
    bad = tmp_path / 'bad.json'
    bad.write_text(json.dumps({'items':[{
        'evidence_id':'ev-12345678','discovered_item_value_redacted':{'token':'supersecrettokenvalue'},'redacted_evidence':{'token':'supersecrettokenvalue'},'redaction_status':'not_sensitive_or_no_secret_literal'
    }]}), encoding='utf-8')
    proc = run([sys.executable, 'quality/secret_redaction_gate.py', '--input', str(bad)])
    assert proc.returncode != 0


def test_schema_accepts_new_evidence_fields(pipeline_out):
    proc = run([sys.executable, 'scripts/evidence-schema-validate.py', str(pipeline_out / 'evidence-manifest.json'), '--kind', 'evidence-manifest'])
    assert proc.returncode == 0, proc.stdout + proc.stderr
