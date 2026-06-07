from __future__ import annotations
from pathlib import Path
from .ast_probe import PROBE_DIR, have, parse_json_stdout, write_temp_source, parse_with_tree_sitter, tree_sitter_available

def parse_functions(source: str, path: str | None = None):
    """Parse Ruby with Ripper, Ruby's standard parser interface."""
    if have('ruby'):
        tmp = Path(path) if path else write_temp_source(source, '.rb')
        try:
            return parse_json_stdout(['ruby', str(PROBE_DIR / 'RubyRipperProbe.rb'), str(tmp)], timeout=20)
        finally:
            if not path:
                try: tmp.unlink()
                except Exception: pass
    if tree_sitter_available('ruby'):
        return parse_with_tree_sitter(source, 'ruby', '.rb')
    return {'status': 'parser_unavailable', 'parser': 'ruby.Ripper_or_tree_sitter_ruby', 'functions': [], 'classes': [], 'calls': [], 'imports': [], 'errors': ['install Ruby or tree_sitter_languages for Ruby AST parsing']}
