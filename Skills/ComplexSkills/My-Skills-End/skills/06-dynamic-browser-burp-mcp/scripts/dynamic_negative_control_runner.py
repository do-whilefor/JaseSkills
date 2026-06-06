#!/usr/bin/env python3
"""Create non-destructive negative-control records from existing dynamic evidence groups.
Does not send network requests. It documents the control obligation for local review."""
from __future__ import annotations
import argparse, json
from pathlib import Path
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('groups_json'); ap.add_argument('--out')
    a=ap.parse_args(); obj=json.loads(Path(a.groups_json).read_text(encoding='utf-8')); groups=obj.get('groups') or obj if isinstance(obj,list) else []
    controls=[{'case_id':g.get('case_id'),'control_type':'negative_control_required','non_destructive':True,'expected_result':'same request with unauthorized/other-tenant/test-safe identifier must not reproduce impact','status':'planned_not_executed_by_this_script'} for g in groups]
    text=json.dumps({'schema_version':'negative_control_plan_v1','controls':controls},ensure_ascii=False,indent=2)
    if a.out: Path(a.out).write_text(text+'\n',encoding='utf-8')
    else: print(text)
if __name__=='__main__': main()
