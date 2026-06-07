#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, output_report, evidence, dry_run_report, read_text
LANG_EXT={'.py':'Python','.js':'JavaScript','.jsx':'JavaScript/React','.ts':'TypeScript','.tsx':'TypeScript/React','.java':'Java','.php':'PHP','.rb':'Ruby','.go':'Go','.rs':'Rust','.cs':'C#','.kt':'Kotlin'}
FRAMEWORK_PATTERNS=[('Express',r'\bexpress\b'),('Next.js',r'\bnext\b'),('React',r'\breact\b'),('Vue',r'\bvue\b'),('Django',r'\bdjango\b'),('FastAPI',r'\bfastapi\b'),('Flask',r'\bflask\b'),('Spring',r'org\.springframework|spring-boot'),('Laravel',r'\blaravel\b|illuminate/'),('Gin',r'github.com/gin-gonic/gin'),('Echo',r'github.com/labstack/echo'),('Actix',r'\bactix\b'),('Rocket',r'\brocket\b')]
MANAGERS={'package.json':'npm/yarn/pnpm','pnpm-lock.yaml':'pnpm','yarn.lock':'yarn','requirements.txt':'pip','pyproject.toml':'Python build backend','pom.xml':'Maven','build.gradle':'Gradle','composer.json':'Composer','Gemfile':'Bundler','go.mod':'Go modules','Cargo.toml':'Cargo'}
BUILD={'vite.config':'Vite','webpack.config':'Webpack','next.config':'Next.js build','Dockerfile':'Docker','docker-compose.yml':'Compose','compose.yml':'Compose','Makefile':'Make','Taskfile.yml':'Taskfile'}

def main():
    ap=common_parser('Identify languages, frameworks, package managers, build tools, runtimes, and module boundaries.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope, root); ok,reason=enforce_scope(root, scope)
    if args.dry_run: return dry_run_report(args,'project_fingerprint',root,scope)
    if not ok: return output_report(args,'project_fingerprint',[evidence('project_fingerprint',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    items=[]; counts={}; frameworks=set(); managers=set(); builds=set(); dirs=set(); topology=set(); workspace_files=[]
    files=list(iter_scoped_files(root, scope, args.max_files, args.timeout, args.scan_profile, args.follow_symlinks)) if root.is_dir() else [root]
    for p in files:
        rel=str(p.relative_to(root)).replace('\\','/') if p.is_relative_to(root) else p.name
        if p.suffix in LANG_EXT:
            counts[LANG_EXT[p.suffix]]=counts.get(LANG_EXT[p.suffix],0)+1
        if p.name in MANAGERS: managers.add(MANAGERS[p.name])
        if p.name in {'pnpm-workspace.yaml','turbo.json','nx.json','rush.json','lerna.json'}:
            topology.add('monorepo_workspace'); workspace_files.append(rel)
        if p.name == 'package.json':
            try:
                pkg=json.loads(read_text(p,300000));
                if isinstance(pkg,dict) and pkg.get('workspaces'):
                    topology.add('monorepo_workspace'); workspace_files.append(rel)
            except Exception:
                pass
        for k,v in BUILD.items():
            if p.name==k or p.name.startswith(k): builds.add(v)
        if len(p.relative_to(root).parts)>1: dirs.add(p.relative_to(root).parts[0])
        text=read_text(p,300000)
        for fw,pat in FRAMEWORK_PATTERNS:
            if re.search(pat,text,re.I): frameworks.add(fw)
    items.append(evidence('project_fingerprint', root, root, 'project_structure', {'top_level_modules':sorted(dirs)[:100], 'file_count_sampled':len(files)}, 1, confidence=.85, linked_report_section='project-fingerprint'))
    if topology:
        items.append(evidence('project_fingerprint', root, root, 'project_topology_detected', {'topologies': sorted(topology), 'workspace_files': sorted(set(workspace_files))}, 1, confidence=.86, linked_report_section='project-fingerprint', reason='Workspace marker files or package.json workspaces indicate monorepo/front-backend package topology', limitation='Static workspace markers do not enumerate every runtime service or deployment boundary'))
    for lang,c in sorted(counts.items()): items.append(evidence('project_fingerprint',root,root,'language_detected',{'language':lang,'files':c},1,confidence=.8,linked_report_section='technology-stack'))
    for fw in sorted(frameworks): items.append(evidence('project_fingerprint',root,root,'framework_detected',fw,1,confidence=.7,linked_report_section='technology-stack'))
    for m in sorted(managers): items.append(evidence('project_fingerprint',root,root,'package_manager_detected',m,1,confidence=.8,linked_report_section='technology-stack'))
    for b in sorted(builds): items.append(evidence('project_fingerprint',root,root,'build_or_runtime_tool_detected',b,1,confidence=.8,linked_report_section='technology-stack'))
    return output_report(args,'project_fingerprint',items,{'summary':{'languages':counts,'frameworks':sorted(frameworks),'package_managers':sorted(managers),'build_tools':sorted(builds),'topologies':sorted(topology)}})
if __name__=='__main__': raise SystemExit(main())
