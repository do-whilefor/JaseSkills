#!/usr/bin/env python3
import argparse, json, re
from pathlib import Path
IGNORE={'.git','node_modules','vendor','dist','build','target','.venv','venv'}
ROUTE_PATTERNS=[r"\b(?:app|router)\.(get|post|put|patch|delete)\(['\"]([^'\"]+)", r"@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\(['\"]?([^'\")]+)", r"@(?:app|router)\.(get|post|put|patch|delete)\(['\"]([^'\"]+)"]
CONFIG_NAMES={'package.json','requirements.txt','pyproject.toml','Pipfile','pom.xml','build.gradle','composer.json','go.mod','Cargo.toml','Gemfile','Dockerfile','docker-compose.yml'}
def iter_files(root):
    for p in root.rglob('*'):
        if any(part in IGNORE for part in p.parts): continue
        if p.is_file(): yield p

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--out', default='project_inventory.json')
    args=ap.parse_args(); root=Path(args.project)
    files=[]; routes=[]; configs=[]
    for p in iter_files(root):
        rel=str(p.relative_to(root)); files.append(rel)
        if p.name in CONFIG_NAMES or p.suffix.lower() in ['.json','.yaml','.yml','.toml','.env']:
            configs.append(rel)
        if p.suffix.lower() in ['.js','.ts','.jsx','.tsx','.py','.java','.php','.rb','.go','.rs'] and p.stat().st_size < 2_000_000:
            txt=p.read_text(encoding='utf-8', errors='ignore')
            for pat in ROUTE_PATTERNS:
                for m in re.finditer(pat, txt):
                    routes.append({'file':rel,'line':txt[:m.start()].count('\n')+1,'match':m.group(0)[:200]})
    out={'root':str(root),'file_count':len(files),'configs':configs,'routes':routes,'notes':'regex 候选，不替代 AST；需 03 进一步确认。'}
    Path(args.out).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
