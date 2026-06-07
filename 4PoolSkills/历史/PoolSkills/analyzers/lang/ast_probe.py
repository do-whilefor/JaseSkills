from __future__ import annotations
import json, os, shutil, subprocess, tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PROBE_DIR = Path(__file__).resolve().parent / 'probes'


def _run(cmd: list[str], timeout: int = 20) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or '', e.stderr or 'timeout'
    except Exception as e:
        return 127, '', str(e)


def write_temp_source(source: str, suffix: str, prefix: str = 'ast_probe_') -> Path:
    fd, name = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(fd)
    p = Path(name)
    p.write_text(source, encoding='utf-8')
    return p


def parse_json_stdout(cmd: list[str], timeout: int = 20) -> dict[str, Any]:
    rc, out, err = _run(cmd, timeout=timeout)
    if rc != 0:
        return {'status': 'parser_error', 'parser': cmd[0], 'functions': [], 'calls': [], 'imports': [], 'errors': [err[:2000]]}
    try:
        data = json.loads(out)
        data.setdefault('functions', [])
        data.setdefault('calls', [])
        data.setdefault('imports', [])
        return data
    except Exception as e:
        return {'status': 'parser_error', 'parser': cmd[0], 'functions': [], 'calls': [], 'imports': [], 'errors': [f'json_parse_error:{e}', out[:1000]]}


def tree_sitter_available(language: str) -> bool:
    try:
        import tree_sitter_languages  # type: ignore
        tree_sitter_languages.get_language(language)
        return True
    except Exception:
        return False


def parse_with_tree_sitter(source: str, language: str, suffix: str) -> dict[str, Any]:
    """Optional tree-sitter adapter. Used only when tree_sitter_languages is installed."""
    try:
        from tree_sitter_languages import get_parser  # type: ignore
        parser = get_parser(language)
        tree = parser.parse(source.encode('utf-8'))
        functions: list[dict[str, Any]] = []
        calls: list[dict[str, Any]] = []
        classes: list[dict[str, Any]] = []

        def text(node):
            return source[node.start_byte:node.end_byte]

        def first_identifier(node):
            stack = [node]
            while stack:
                n = stack.pop(0)
                if n.type in {'identifier', 'field_identifier', 'constant', 'type_identifier'}:
                    return text(n)
                stack[0:0] = list(n.children)
            return None

        def walk(node):
            if node.type in {'function_item', 'function_declaration', 'method_declaration', 'function_definition', 'method', 'singleton_method', 'function'}:
                functions.append({'name': first_identifier(node) or '<anonymous>', 'line': node.start_point[0] + 1, 'end_line': node.end_point[0] + 1, 'kind': node.type})
            if node.type in {'class_declaration', 'class', 'class_definition'}:
                classes.append({'name': first_identifier(node) or '<anonymous>', 'line': node.start_point[0] + 1, 'end_line': node.end_point[0] + 1, 'kind': node.type})
            if node.type in {'call_expression', 'method_invocation', 'command', 'command_call'}:
                calls.append({'name': first_identifier(node) or '<call>', 'line': node.start_point[0] + 1, 'kind': node.type})
            for c in node.children:
                walk(c)
        walk(tree.root_node)
        return {'status': 'parsed', 'parser': f'tree_sitter_languages.{language}', 'functions': functions, 'classes': classes, 'calls': calls, 'imports': [], 'errors': []}
    except Exception as e:
        return {'status': 'parser_error', 'parser': f'tree_sitter_languages.{language}', 'functions': [], 'calls': [], 'imports': [], 'errors': [str(e)]}


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None
