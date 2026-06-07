from __future__ import annotations
from pathlib import Path
from .ast_probe import PROBE_DIR, have, parse_json_stdout, write_temp_source


def parse_functions(source: str, path: str | None = None):
    """Parse JavaScript/TypeScript through the TypeScript compiler API.

    No regex fallback is used. If node/typescript is unavailable, the adapter returns parser_unavailable.
    """
    if not have('node'):
        return {'status':'parser_unavailable','parser':'typescript.compiler_api','functions':[],'classes':[],'calls':[],'imports':[],'errors':['node_not_available']}
    tmp = Path(path) if path else write_temp_source(source, '.ts')
    try:
        data = parse_json_stdout(['node', str(PROBE_DIR / 'TypeScriptAstProbe.js'), str(tmp)], timeout=20)
        if data.get('status') == 'parser_error':
            data['parser'] = 'typescript.compiler_api'
        return data
    finally:
        if not path:
            try: tmp.unlink()
            except Exception: pass
