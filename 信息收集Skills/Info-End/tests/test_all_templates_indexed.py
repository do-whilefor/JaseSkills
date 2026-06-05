import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_all_templates_are_indexed_exactly_once():
    data=json.loads((ROOT/'manifests/template_index.json').read_text())
    indexed=[t['path'] for t in data['templates']]
    actual=[str(p.relative_to(ROOT)).replace('\\','/') for p in sorted((ROOT/'templates').glob('*.md'))]
    assert sorted(indexed) == sorted(actual)
    assert len(indexed) == len(set(indexed))
