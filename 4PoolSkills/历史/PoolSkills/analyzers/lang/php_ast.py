from __future__ import annotations
import json, subprocess
from pathlib import Path
from .ast_probe import PROBE_DIR, have, parse_with_tree_sitter, tree_sitter_available, write_temp_source

def _project_root(path: Path) -> Path:
    cur = path.resolve().parent if path.exists() else Path.cwd().resolve()
    for p in [cur] + list(cur.parents):
        if (p / 'composer.json').exists() or (p / 'vendor' / 'autoload.php').exists():
            return p
    return cur

def _run_nikic(tmp: Path) -> dict:
    project = _project_root(tmp)
    cmd = ['php', str(PROBE_DIR / 'PhpNikicAstProbe.php'), str(tmp), str(project)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=str(project))
    except Exception as e:
        return {'status':'parser_error','parser':'nikic/php-parser','functions':[],'classes':[],'calls':[],'imports':[],'errors':[str(e)]}
    if p.returncode != 0:
        return {'status':'parser_unavailable','parser':'nikic/php-parser','functions':[],'classes':[],'calls':[],'imports':[],'errors':[p.stderr.strip() or p.stdout.strip() or f'exit_code={p.returncode}']}
    try:
        data=json.loads(p.stdout)
        data.setdefault('functions',[]); data.setdefault('classes',[]); data.setdefault('calls',[]); data.setdefault('imports',[]); data.setdefault('errors',[])
        return data
    except Exception as e:
        return {'status':'parser_error','parser':'nikic/php-parser','functions':[],'classes':[],'calls':[],'imports':[],'errors':[f'json_parse_error:{e}', p.stdout[:1000]]}

def parse_functions(source: str, path: str | None = None):
    """Parse PHP with tree-sitter or nikic/php-parser only. No structural tokenizer fallback is reported as full AST."""
    if tree_sitter_available('php'):
        return parse_with_tree_sitter(source, 'php', '.php')
    if have('php'):
        tmp = Path(path) if path else write_temp_source(source, '.php')
        try:
            return _run_nikic(tmp)
        finally:
            if not path:
                try: tmp.unlink()
                except Exception: pass
    return {'status':'parser_unavailable','parser':'tree_sitter_php_or_nikic_php_parser','functions':[],'classes':[],'calls':[],'imports':[],'errors':['install PHP CLI plus composer dependency nikic/php-parser, or tree_sitter_languages with PHP grammar']}
