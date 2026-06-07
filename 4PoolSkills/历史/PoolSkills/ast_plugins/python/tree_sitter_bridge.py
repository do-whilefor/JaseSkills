#!/usr/bin/env python3
import json, sys, pathlib
try:
    import tree_sitter  # noqa
except Exception as e:
    print(json.dumps({'status':'missing','plugin':'tree_sitter','error':'missing tree_sitter: '+str(e),'nodes':[],'edges':[]})); raise SystemExit(0)
file = pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else None
if not file or not file.exists():
    print(json.dumps({'status':'failed','plugin':'tree_sitter','error':'missing input file','nodes':[],'edges':[]})); raise SystemExit(0)
print(json.dumps({'status':'degraded','plugin':'tree_sitter','file':str(file),'note':'tree_sitter installed; language grammar package not assumed. Configure grammar before ready.','nodes':[{'id':str(file),'type':'file','file':str(file)}],'edges':[]}, indent=2))
