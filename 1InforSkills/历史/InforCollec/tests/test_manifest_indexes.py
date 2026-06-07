#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_template_index_paths_exist():
    data=json.loads((ROOT/'manifests/template_index.json').read_text(encoding='utf-8'))
    missing=[t['path'] for t in data['templates'] if not (ROOT/t['path']).exists()]
    assert not missing

def test_knowledge_index_paths_exist_except_queue():
    data=json.loads((ROOT/'manifests/knowledge_index.json').read_text(encoding='utf-8'))
    missing=[e['path'] for e in data['entries'] if not (ROOT/e['path']).exists()]
    assert not missing
    assert (ROOT/data['human_review_queue']).exists()
