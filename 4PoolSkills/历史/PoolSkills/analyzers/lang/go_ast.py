from __future__ import annotations
from pathlib import Path
from .ast_probe import PROBE_DIR, have, parse_json_stdout, write_temp_source, parse_with_tree_sitter, tree_sitter_available

def parse_functions(source: str, path: str | None = None):
    """Parse Go with standard library go/parser through a tiny local probe."""
    if have('go'):
        tmp = Path(path) if path else write_temp_source(source, '.go')
        try:
            return parse_json_stdout(['go', 'run', str(PROBE_DIR / 'GoAstProbe.go'), '--', str(tmp)], timeout=30)
        finally:
            if not path:
                try: tmp.unlink()
                except Exception: pass
    if tree_sitter_available('go'):
        return parse_with_tree_sitter(source, 'go', '.go')
    return {'status': 'parser_unavailable', 'parser': 'go/parser_or_tree_sitter_go', 'functions': [], 'classes': [], 'calls': [], 'imports': [], 'errors': ['install Go toolchain or tree_sitter_languages for Go AST parsing']}
