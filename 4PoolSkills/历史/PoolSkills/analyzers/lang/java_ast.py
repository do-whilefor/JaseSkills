from __future__ import annotations
import subprocess, tempfile
from pathlib import Path
from .ast_probe import PROBE_DIR, have, parse_json_stdout, write_temp_source, parse_with_tree_sitter, tree_sitter_available

_COMPILED = False

def _compile_probe() -> bool:
    global _COMPILED
    if _COMPILED:
        return True
    if not have('javac') or not have('java'):
        return False
    src = PROBE_DIR / 'JavaAstProbe.java'
    cls = PROBE_DIR / 'JavaAstProbe.class'
    if cls.exists() and cls.stat().st_mtime >= src.stat().st_mtime:
        _COMPILED = True
        return True
    p = subprocess.run(['javac', str(src)], capture_output=True, text=True, timeout=20)
    _COMPILED = p.returncode == 0
    return _COMPILED

def parse_functions(source: str, path: str | None = None):
    """Parse Java with javac TreeScanner. Falls back to tree-sitter only if installed; never labels regex as AST."""
    if _compile_probe():
        tmp = Path(path) if path else write_temp_source(source, '.java')
        try:
            return parse_json_stdout(['java', '-cp', str(PROBE_DIR), 'JavaAstProbe', str(tmp)], timeout=25)
        finally:
            if not path:
                try: tmp.unlink()
                except Exception: pass
    if tree_sitter_available('java'):
        return parse_with_tree_sitter(source, 'java', '.java')
    return {'status': 'parser_unavailable', 'parser': 'javac.TreeScanner_or_tree_sitter_java', 'functions': [], 'classes': [], 'calls': [], 'imports': [], 'errors': ['install JDK javac or tree_sitter_languages for Java AST parsing']}
