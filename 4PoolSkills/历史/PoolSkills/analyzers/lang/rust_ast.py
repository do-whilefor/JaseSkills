from __future__ import annotations
import json, subprocess
from pathlib import Path
from .ast_probe import PROBE_DIR, have, parse_with_tree_sitter, tree_sitter_available, write_temp_source

def _run_syn_bridge(tmp: Path) -> dict:
    manifest = PROBE_DIR / 'rust_syn_bridge' / 'Cargo.toml'
    if not manifest.exists() or not have('cargo'):
        return {'status':'parser_unavailable','parser':'syn_full','functions':[],'classes':[],'calls':[],'imports':[],'errors':['cargo or rust syn bridge unavailable']}
    cmd=['cargo','run','--offline','--quiet','--manifest-path',str(manifest),'--',str(tmp)]
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=20)
    except Exception as e:
        return {'status':'parser_error','parser':'syn_full','functions':[],'classes':[],'calls':[],'imports':[],'errors':[str(e)]}
    if p.returncode != 0:
        return {'status':'parser_unavailable','parser':'syn_full','functions':[],'classes':[],'calls':[],'imports':[],'errors':[p.stderr[:2000] or p.stdout[:1000]]}
    try:
        data=json.loads(p.stdout)
        data.setdefault('functions',[]); data.setdefault('classes',[]); data.setdefault('calls',[]); data.setdefault('imports',[]); data.setdefault('errors',[])
        return data
    except Exception as e:
        return {'status':'parser_error','parser':'syn_full','functions':[],'classes':[],'calls':[],'imports':[],'errors':[f'json_parse_error:{e}', p.stdout[:1000]]}

def parse_functions(source: str, path: str | None = None):
    """Parse Rust with tree-sitter or syn full parser. No regex fallback."""
    if tree_sitter_available('rust'):
        return parse_with_tree_sitter(source, 'rust', '.rs')
    tmp = Path(path) if path else write_temp_source(source, '.rs')
    try:
        data=_run_syn_bridge(tmp)
        if data.get('status') == 'parsed':
            return data
        if have('rustc'):
            p=subprocess.run(['rustc','-Z','unpretty=ast-tree',str(tmp)],capture_output=True,text=True,timeout=20)
            if p.returncode == 0:
                return {'status':'parsed','parser':'rustc_nightly_ast_tree','functions':[],'classes':[],'calls':[],'imports':[],'raw_ast_summary':p.stdout[:4000],'errors':[]}
        return data
    finally:
        if not path:
            try: tmp.unlink()
            except Exception: pass
