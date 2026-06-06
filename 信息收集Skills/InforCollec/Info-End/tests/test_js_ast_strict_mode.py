import subprocess, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_js_ast_strict_mode_is_honest_about_backend(tmp_path):
    out=tmp_path/'strict.jsonl'
    proc=subprocess.run(['node',str(ROOT/'scripts/js-ast-endpoint-extractor.mjs'),str(ROOT/'tests/fixtures/js_ast_app'),'--strict-ast','-o',str(out)],text=True,capture_output=True)
    if proc.returncode == 0:
        rows=[json.loads(x) for x in out.read_text().splitlines() if x.strip()]
        assert rows and all(r['parser_mode']=='babel_ast_walk' for r in rows)
    else:
        assert proc.returncode in (3,4)
        assert 'strict AST' in proc.stderr or 'AST parse failed' in proc.stderr
