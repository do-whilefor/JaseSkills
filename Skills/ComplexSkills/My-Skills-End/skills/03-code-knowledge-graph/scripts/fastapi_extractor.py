#!/usr/bin/env python3
"""fastapi extractor wrapper around semantic_graph_builder."""
from pathlib import Path
import argparse, json, sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from semantic_graph_builder import build

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('project')
    ap.add_argument('--out', required=True)
    args=ap.parse_args()
    result=build(args.project, 'fastapi')
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'framework': 'fastapi', 'routes': len(result.get('routes', [])), 'out': args.out}, ensure_ascii=False))
if __name__ == '__main__': main()
