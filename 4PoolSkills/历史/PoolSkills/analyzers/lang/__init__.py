from __future__ import annotations
from pathlib import Path

LANG_BY_EXT = {
    '.py': 'python_ast', '.js': 'js_ts_ast', '.jsx': 'js_ts_ast', '.ts': 'js_ts_ast', '.tsx': 'js_ts_ast',
    '.java': 'java_ast', '.php': 'php_ast', '.go': 'go_ast', '.rs': 'rust_ast', '.rb': 'ruby_ast'
}

def parse_source(path: str | Path, source: str):
    ext = Path(path).suffix.lower()
    modname = LANG_BY_EXT.get(ext)
    if not modname:
        return {'status': 'unsupported_language', 'parser': None, 'functions': [], 'classes': [], 'calls': [], 'imports': [], 'errors': []}
    mod = __import__(f'analyzers.lang.{modname}', fromlist=['parse_functions'])
    try:
        return mod.parse_functions(source, str(path))
    except TypeError:
        return mod.parse_functions(source)
