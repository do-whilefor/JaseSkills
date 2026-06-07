#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys, shutil, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'; OUT.mkdir(exist_ok=True)
EXT = {'.js':['babel_js'],'.jsx':['babel_js'],'.mjs':['babel_js'],'.cjs':['babel_js'],'.ts':['typescript_compiler','babel_js'],'.tsx':['typescript_compiler','babel_js'],'.py':['python_ast_libcst'],'.rb':['ruby_ripper'],'.go':['go_parser'],'.rs':['rust_syn'],'.php':['php_parser'],'.java':['javaparser']}
BRIDGES = {'babel_js':['node',str(ROOT/'ast_plugins/js/babel_route_bridge.js')],'typescript_compiler':['node',str(ROOT/'ast_plugins/js/typescript_route_bridge.js')],'python_ast_libcst':[sys.executable,str(ROOT/'ast_plugins/python/python_ast_libcst_bridge.py')],'tree_sitter':[sys.executable,str(ROOT/'ast_plugins/python/tree_sitter_bridge.py')],'ruby_ripper':['ruby',str(ROOT/'ast_plugins/ruby/ripper_bridge.rb')],'go_parser':['go','run',str(ROOT/'ast_plugins/go/go_parser_bridge.go')],'rust_syn':['cargo','run','--quiet','--manifest-path',str(ROOT/'ast_plugins/rust/rust_syn_bridge/Cargo.toml'),'--'],'php_parser':['php',str(ROOT/'ast_plugins/php/php_parser_bridge.php')]}
SKIP_DIRS={'.git','node_modules','vendor','target','dist','build','.next','coverage','raw_original_sources','raw_original_kb_templates','_backup','outputs'}

def java_cmd(file: Path):
    if not shutil.which('javac') or not shutil.which('java'):
        return None, 'missing executable: javac/java'
    classes=OUT/'java_bridge_classes'; classes.mkdir(parents=True, exist_ok=True)
    src=ROOT/'ast_plugins/java/javaparser_bridge.java'
    cp=os.environ.get('JAVAPARSER_CLASSPATH','')
    javac=['javac','-d',str(classes)]
    if cp: javac += ['-cp', cp]
    javac.append(str(src))
    r=subprocess.run(javac, cwd=str(ROOT), text=True, capture_output=True, timeout=30)
    if r.returncode!=0:
        return None, 'javac failed: '+(r.stderr.strip() or r.stdout.strip())[:800]
    run_cp=str(classes) + ((os.pathsep + cp) if cp else '')
    return ['java','-cp',run_cp,'javaparser_bridge',str(file)], None

def run_bridge(plugin, file):
    if plugin=='javaparser':
        cmd, err = java_cmd(Path(file))
        if err: return {'schema_version':'phase4-security-graph-v2','status':'missing','plugin':plugin,'file':str(file),'error':err,'nodes':[],'edges':[]}
    else:
        cmd = BRIDGES[plugin] + [str(file)]
    if not shutil.which(cmd[0]): return {'schema_version':'phase4-security-graph-v2','status':'missing','plugin':plugin,'file':str(file),'error':'missing executable: '+cmd[0],'nodes':[],'edges':[]}
    try:
        r=subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=30)
        text=r.stdout.strip() or r.stderr.strip()
        data=json.loads(text)
        data.setdefault('schema_version','phase4-security-graph-v2')
        return data
    except Exception as e:
        return {'schema_version':'phase4-security-graph-v2','status':'failed','plugin':plugin,'file':str(file),'error':str(e),'stdout':locals().get('text','')[:500],'nodes':[],'edges':[]}

def scan(project):
    project=Path(project).resolve(); results=[]; nodes=[]; edges=[]
    for p in project.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in EXT: continue
        if any(part in SKIP_DIRS for part in p.parts): continue
        for plugin in EXT[p.suffix.lower()]:
            res=run_bridge(plugin,p); results.append(res); nodes.extend(res.get('nodes',[]) or []); edges.extend(res.get('edges',[]) or [])
            if res.get('status') in ['ready','degraded'] and (res.get('nodes') or res.get('edges')): break
    # Fallback: when language-specific AST tooling is unavailable or the project uses framework forms
    # not covered by a bridge, use route_extractor.py to generate conservative Route -> Handler nodes.
    node_types={n.get('type') for n in nodes}; edge_types={e.get('type') for e in edges}
    if not ({'route','handler'}.issubset(node_types) and 'ROUTE_TO_HANDLER' in edge_types):
        try:
            attack_out=OUT/'attack_surface_for_graph.json'
            rr=subprocess.run([sys.executable, str(ROOT/'scripts/route_extractor.py'), str(project), '--out', str(attack_out)], cwd=str(ROOT), text=True, capture_output=True, timeout=30)
            attack=json.loads(attack_out.read_text(encoding='utf-8')) if attack_out.exists() else {}
            for r in attack.get('routes',[]):
                rid=f"{r.get('file')}:{r.get('method')} {r.get('route')}"
                hid=f"{r.get('file')}:handler:{r.get('line')}"
                nodes.append({'id':rid,'type':'route','file':r.get('file'),'method':r.get('method'),'route':r.get('route'),'framework_hint':r.get('framework_hint'),'line':r.get('line'),'source':'route_extractor_fallback'})
                nodes.append({'id':hid,'type':'handler','file':r.get('file'),'name':r.get('handler_hint') or 'framework_handler','line':r.get('line'),'source':'route_extractor_fallback'})
                edges.append({'from':rid,'to':hid,'type':'ROUTE_TO_HANDLER','source':'route_extractor_fallback'})
                for param in r.get('parameters',[]) or []:
                    pid=f"{rid}:param:{param}"; nodes.append({'id':pid,'type':'parameter','file':r.get('file'),'name':param,'source':'route_extractor_fallback'}); edges.append({'from':rid,'to':pid,'type':'READS_PARAMETER','source':'route_extractor_fallback'})
            if attack.get('routes'):
                results.append({'schema_version':'phase4-security-graph-v2','status':'ready','plugin':'route_extractor_fallback','file':str(project),'nodes_added':len(attack.get('routes',[]))*2,'edges_added':len(attack.get('routes',[])),'stdout':rr.stdout[-500:]})
        except Exception as e:
            results.append({'schema_version':'phase4-security-graph-v2','status':'failed','plugin':'route_extractor_fallback','file':str(project),'error':str(e),'nodes':[],'edges':[]})
    node_types={n.get('type') for n in nodes}; edge_types={e.get('type') for e in edges}
    degraded_plugins=[r for r in results if r.get('status')=='degraded']
    quality={
        'has_route': 'route' in node_types,
        'has_handler': 'handler' in node_types,
        'has_route_to_handler': 'ROUTE_TO_HANDLER' in edge_types,
        'degraded_plugin_count': len(degraded_plugins),
        'degraded_reasons': [r.get('degraded_reason') or r.get('fallback_reason') for r in degraded_plugins if r.get('degraded_reason') or r.get('fallback_reason')],
        'status': 'pass' if {'route','handler'}.issubset(node_types) and 'ROUTE_TO_HANDLER' in edge_types else 'degraded',
        'confirmation_policy': 'degraded graph nodes are candidate-only and cannot confirm vulnerabilities without manifest v4 dynamic evidence and negative controls'
    }
    graph={'schema_version':'phase4-security-graph-v2','project':str(project),'nodes':nodes,'edges':edges,'plugin_results':results,'quality':quality,'policy':'graph evidence is candidate-only; confirmation requires manifest v4 dynamic evidence and negative controls'}
    (OUT/'security_graph.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'semantic_ast_status.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'ok','files_analyzed':len({r.get('file') for r in results if r.get('file')}),'nodes':len(nodes),'edges':len(edges),'quality':quality,'graph':str(OUT/'security_graph.json')},ensure_ascii=False,indent=2))
    return 0 if quality['status']=='pass' else 1
if __name__=='__main__': raise SystemExit(scan(sys.argv[1] if len(sys.argv)>1 else ROOT/'examples'))
