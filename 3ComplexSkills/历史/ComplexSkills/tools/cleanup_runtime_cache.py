#!/usr/bin/env python3
from __future__ import annotations
import json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    removed=[]
    for p in list(ROOT.rglob('__pycache__')):
        if p.is_dir(): shutil.rmtree(p); removed.append(str(p.relative_to(ROOT)))
    for p in list(ROOT.rglob('*.py[co]')):
        if p.is_file(): removed.append(str(p.relative_to(ROOT))); p.unlink()
    print(json.dumps({'schema_version':'runtime_cache_cleanup_v1','removed':removed,'removed_count':len(removed)},ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__': raise SystemExit(main())
