import sys
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_codegraph_builder_links_python_route_to_handler(tmp_path):
    out=tmp_path/'graph.json'
    subprocess.run([sys.executable, str(ROOT/'scripts/codegraph-builder.py'), str(ROOT/'tests/fixtures/codegraph_app'), '-o', str(out)], check=True)
    g=json.loads(out.read_text())
    assert g['summary']['node_count'] >= 2
    assert any(n.get('type') == 'route' and n.get('path') == '/api/projects/<project_id>' for n in g['nodes'])
    assert any(e.get('type') == 'route_to_handler' for e in g['edges'])
