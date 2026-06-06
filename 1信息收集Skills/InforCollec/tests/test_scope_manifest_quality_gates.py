from __future__ import annotations
import json, os, subprocess, sys, tempfile
import pytest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PY=sys.executable

def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, **kw)

def test_default_scan_includes_frontend_artifacts():
    out=run([PY,'scripts/frontend_artifact_graph.py','--input','tests/fixtures/artifact_scan_app','--scope','tests/fixtures/artifact_scan_app','--format','json'], check=True)
    data=json.loads(out.stdout)
    blob=json.dumps(data,ensure_ascii=False)
    assert '/api/hidden-from-next-chunk' in blob
    assert '/api/dist-hidden' in blob

def test_iter_scoped_files_blocks_symlink_to_out_of_scope(tmp_path):
    allowed=tmp_path/'allowed'; outside=tmp_path/'outside'; allowed.mkdir(); outside.mkdir()
    (outside/'secret.txt').write_text('PASSWORD=SuperSecretValue123',encoding='utf-8')
    (allowed/'local.txt').write_text('/api/local',encoding='utf-8')
    try:
        (allowed/'linked_secret.txt').symlink_to(outside/'secret.txt')
    except OSError:
        return
    out=tmp_path/'scope.json'
    run([PY,'scripts/hidden_info_collector.py','--input',str(allowed),'--scope',str(allowed),'--output',str(out),'--format','json'], check=True)
    data=json.loads(out.read_text())
    blob=json.dumps(data,ensure_ascii=False)
    assert 'SuperSecretValue123' not in blob
    assert 'linked_secret' not in blob


def test_quality_gate_fails_generic_unredacted_secret(tmp_path):
    manifest=tmp_path/'bad.json'
    item={
      'evidence_id':'ev-'+'a'*16,'kind':'information_surface','collector_name':'unit','skill_name':'Info-End','source_file':'a.env','source_line_start':1,'source_line_end':1,'source_type':'source','discovered_item_type':'secret_name_signal','discovered_item_value_redacted':'PASSWORD=MyUltraSecret987654321','raw_value_hash':'b'*64,'confidence':0.9,'severity_hint':'info','auth_relevance':'unknown','tenant_relevance':'unknown','role_relevance':'unknown','endpoint_relevance':'unknown','data_sensitivity':'high','reproduction_hint':'local','collection_time':'2026-01-01T00:00:00+00:00','scope_id':'unit','false_positive_reason':'','needs_human_review':True,'linked_report_section':'configuration-deployment','path':'a.env','redaction_status':'not_sensitive_or_no_secret_literal','collector_provenance':{'collector':'unit','source':'test','network':'disabled'}
    }
    items=[]
    sections=['authorization-scope','project-fingerprint','technology-stack','route-api-inventory','frontend-js','configuration-deployment','auth-role-tenant','hidden-information','dependency-surface','evidence-index']
    for i,sec in enumerate(sections):
        safe=dict(item); safe['evidence_id']='ev-'+hex(i+1)[2:].rjust(16,'0'); safe['discovered_item_value_redacted']='safe'; safe['raw_value_hash']=str(i).rjust(64,'0'); safe['linked_report_section']=sec; safe['redaction_status']='not_sensitive_or_no_secret_literal'; items.append(safe)
    items.append(item)
    manifest.write_text(json.dumps({'schema_version':'1.0','project':{'name':'u','root':str(tmp_path),'base_urls':[]},'generated_at':'2026-01-01T00:00:00+00:00','items':items}),encoding='utf-8')
    r=run([PY,'scripts/info_quality_gate.py','--input',str(manifest),'--scope',str(tmp_path),'--min-score','70'])
    assert r.returncode != 0
    assert 'unredacted_secret_detected' in r.stdout


def test_schema_validator_rejects_incomplete_manifest(tmp_path):
    p=tmp_path/'bad.json'; p.write_text(json.dumps({'schema_version':'1.0','project':{'name':'x','root':'x','base_urls':[]},'generated_at':'x','items':[{'evidence_id':'ev-12345678'}]}),encoding='utf-8')
    r=run([PY,'scripts/evidence-schema-validate.py',str(p),'--kind','evidence-manifest'])
    assert r.returncode != 0
    assert 'collector_name' in r.stdout


def test_framework_route_extractors_cover_multiple_frameworks():
    r=run([PY,'scripts/framework_route_extractors.py','--input','tests/fixtures/top_tier_info_app','--scope','tests/fixtures/top_tier_info_app','--format','json'], check=True)
    blob=r.stdout
    assert 'FastAPI' in blob
    assert 'Spring' in blob
    assert 'Laravel' in blob
    assert 'Go' in blob
    assert 'Rust' in blob
    assert 'NestJS' in blob


@pytest.mark.skip(reason="orchestrator is validated by scripts/top-tier-smoke-test.py and manual command to avoid nested subprocess stalls in constrained pytest runners")
def test_orchestrator_generates_manifest_quality_report_dashboard(tmp_path):
    out=tmp_path/'out'
    r=subprocess.run([PY,'scripts/info_collect_orchestrator.py','--input','tests/fixtures/top_tier_info_app','--scope','tests/fixtures/top_tier_info_app','--output',str(out),'--timeout','2','--max-files','1000'], cwd=ROOT, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=90)
    assert r.returncode == 0, r.stderr
    for name in ['evidence-manifest.json','info-quality-gate.json','human-review-queue.json','info-report.md','dashboard.html','orchestrator-summary.json']:
        assert (out/name).exists()
    q=json.loads((out/'info-quality-gate.json').read_text())
    assert q['status']=='PASS'
