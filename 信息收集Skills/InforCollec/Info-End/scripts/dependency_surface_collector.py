#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, re
from _info_collect_lib import common_parser, parse_scope, enforce_scope, iter_scoped_files, output_report, evidence, dry_run_report, read_text, line_no
DANGEROUS=re.compile(r'(?i)\b(postinstall|preinstall|prepare|install|curl|wget|bash|sh\s+-c|eval\(|child_process|execSync|vm2|node-gyp|loader|plugin|dynamic import|import\(|require\()\b')
RISKY_DEP=re.compile(r'(?i)\b(request|lodash|serialize-javascript|node-serialize|yaml|js-yaml|express-fileupload|multer|formidable|shelljs|execa|vm2|node-forge|jsonwebtoken|passport|spring-security|commons-collections)\b')
def main():
    ap=common_parser('Collect dependency, supply-chain, build-script, postinstall, plugin, loader and dynamic import risk signals.')
    args=ap.parse_args(); root=Path(args.input).resolve(); scope=parse_scope(args.scope, root); ok,reason=enforce_scope(root, scope)
    if args.dry_run: return dry_run_report(args,'dependency_surface_collector',root,scope)
    if not ok: return output_report(args,'dependency_surface_collector',[evidence('dependency_surface_collector',root,root.parent,'out_of_scope_blocked',reason,1,confidence=1,severity_hint='blocker',needs_review=True)], {'scope_check':'FAIL'}) or 2
    items=[]
    for p in (iter_scoped_files(root, scope, args.max_files, args.timeout, args.scan_profile, args.follow_symlinks) if root.is_dir() else [root]):
        text=read_text(p); name=p.name.lower()
        if name in {'package.json','composer.json','gemfile','go.mod','cargo.toml','pom.xml','build.gradle','requirements.txt','pyproject.toml'}:
            items.append(evidence('dependency_surface_collector',p,root,'dependency_manifest',p.name,1,confidence=.9,linked_report_section='dependency-surface'))
            if name=='package.json':
                try:
                    data=json.loads(text)
                    for s,cmd in (data.get('scripts') or {}).items():
                        if DANGEROUS.search(s+' '+str(cmd)): items.append(evidence('dependency_surface_collector',p,root,'dangerous_package_script', {s:cmd}, 1, confidence=.75, severity_hint='medium', needs_review=True, linked_report_section='dependency-surface'))
                    for section in ['dependencies','devDependencies','optionalDependencies']:
                        for k,v in (data.get(section) or {}).items():
                            if RISKY_DEP.search(k): items.append(evidence('dependency_surface_collector',p,root,'risky_dependency_signal', {k:v,'section':section}, 1, confidence=.6, needs_review=True, linked_report_section='dependency-surface'))
                except Exception: pass
        for m in DANGEROUS.finditer(text):
            items.append(evidence('dependency_surface_collector',p,root,'build_or_runtime_dangerous_construct',m.group(0),line_no(text,m.group(0)),confidence=.55,severity_hint='medium',needs_review=True,linked_report_section='dependency-surface'))
    return output_report(args,'dependency_surface_collector',items)
if __name__=='__main__': raise SystemExit(main())
