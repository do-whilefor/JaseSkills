#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, shutil, subprocess, time, hashlib, os
from pathlib import Path
from typing import Any

LOCAL_OSS_CANDIDATES = [
  {'slug':'novnc-webutil','name':'noVNC webutil module','root':'/opt/novnc/app','files':['webutil.js']},
  {'slug':'novnc-websock','name':'noVNC websocket module','root':'/opt/novnc/core','files':['websock.js']},
  {'slug':'sphinx-theme-extras','name':'Sphinx theme extras','root':'/usr/share/javascript/sphinxdoc/1.0','files':['theme_extras.js']},
  {'slug':'sphinx-sidebar','name':'Sphinx sidebar','root':'/usr/share/javascript/sphinxdoc/1.0','files':['sidebar.js']},
  {'slug':'sphinx-doctools','name':'Sphinx doctools','root':'/usr/share/javascript/sphinxdoc/1.0','files':['doctools.js']},
  {'slug':'sphinx-language-data','name':'Sphinx language data','root':'/usr/share/javascript/sphinxdoc/1.0','files':['language_data.js']},
  {'slug':'sphinx-highlight','name':'Sphinx highlight','root':'/usr/share/javascript/sphinxdoc/1.0','files':['sphinx_highlight.js']},
  {'slug':'gitweb-static','name':'Gitweb static JavaScript','root':'/usr/share/gitweb/static','files':['gitweb.js']},
  {'slug':'texinfo-modernizr','name':'Texinfo bundled Modernizr','root':'/usr/share/texinfo/js','files':['modernizr.js']},
  {'slug':'asymptote-reload','name':'Asymptote reload JavaScript','root':'/usr/share/asymptote','files':['reload.js']},
  {'slug':'inkscape-inkweb','name':'Inkscape InkWeb JavaScript','root':'/usr/share/inkscape/extensions','files':['inkweb.js']},
  {'slug':'inkscape-jessyink-core','name':'Inkscape JessyInk core JavaScript','root':'/usr/share/inkscape/extensions','files':['jessyInk_core_mouseHandler_noclick.js']},
]

def run(cmd, cwd: Path, timeout=120):
    st=time.time()
    try:
        p=subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {'cmd':cmd,'returncode':p.returncode,'stdout_tail':p.stdout[-2000:],'stderr_tail':p.stderr[-2000:],'elapsed_sec':round(time.time()-st,3)}
    except Exception as e:
        return {'cmd':cmd,'returncode':124,'stdout_tail':'','stderr_tail':str(e),'elapsed_sec':round(time.time()-st,3)}


def load(p: Path, default=None):
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return default if default is not None else {}


def sha(p: Path):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()


def dpkg_owner(path: Path):
    try:
        p=subprocess.run(['dpkg','-S',str(path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=10)
        if p.returncode==0 and ':' in p.stdout:
            return p.stdout.split(':',1)[0].split(',')[0].strip()
    except Exception:
        pass
    return ''


def doc_copyright_for(pkg: str):
    if not pkg: return None
    cand=Path('/usr/share/doc')/pkg/'copyright'
    return cand if cand.exists() else None


def copy_candidate(cand: dict[str,Any], base: Path):
    src_root=Path(cand['root'])
    dest=base/cand['slug']
    dest.mkdir(parents=True, exist_ok=True)
    copied=[]; missing=[]; file_hashes=[]; owner=''
    if not src_root.exists():
        return {'slug':cand['slug'],'name':cand['name'],'status':'missing','source_root':str(src_root),'missing_root':True,'copied_files':[],'missing_files':cand.get('files',[])}
    for rel in cand.get('files',[]):
        src=src_root/rel; dst=dest/rel
        if src.exists() and src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src,dst); copied.append(rel); file_hashes.append({'path':rel,'sha256':sha(dst),'size':dst.stat().st_size})
            owner=owner or dpkg_owner(src)
        else:
            missing.append(rel)
    for lic in ['LICENSE','LICENSE.txt','COPYING','README.md','package.json']:
        src=src_root/lic
        if src.exists() and src.is_file() and lic not in copied:
            shutil.copy2(src,dest/lic); copied.append(lic); file_hashes.append({'path':lic,'sha256':sha(dest/lic),'size':(dest/lic).stat().st_size})
    cp=doc_copyright_for(owner)
    if cp:
        shutil.copy2(cp, dest/'DEBIAN_COPYRIGHT')
        copied.append('DEBIAN_COPYRIGHT'); file_hashes.append({'path':'DEBIAN_COPYRIGHT','sha256':sha(dest/'DEBIAN_COPYRIGHT'),'size':(dest/'DEBIAN_COPYRIGHT').stat().st_size})
    # Add minimal HTML entry if none exists so collector can discover scripts in package root.
    if not any(Path(x).suffix.lower() in {'.html','.htm'} for x in copied):
        jsfiles=[x for x in copied if Path(x).suffix.lower()=='.js'][:5]
        html='<!doctype html><meta charset="utf-8"><title>{}</title>\n'.format(cand['name']) + '\n'.join(f'<script src="{j}"></script>' for j in jsfiles)
        (dest/'index.html').write_text(html+'\n', encoding='utf-8'); copied.append('index.html'); file_hashes.append({'path':'index.html','sha256':sha(dest/'index.html'),'size':(dest/'index.html').stat().st_size})
    provenance={'schema_version':'real-oss-source-provenance/v2','slug':cand['slug'],'project':cand['name'],'source_root':str(src_root),'snapshot_path':str(dest),'dpkg_owner':owner,'copied_files':copied,'missing_files':missing,'file_hashes':file_hashes,'license_or_copyright_file':'DEBIAN_COPYRIGHT' if (dest/'DEBIAN_COPYRIGHT').exists() else ('LICENSE.txt' if (dest/'LICENSE.txt').exists() else ''),'note':'Local installed open-source package/source subset copied for deterministic static replay. This is not a user authorized web target runtime replay.'}
    (dest/'oss-provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'slug':cand['slug'],'name':cand['name'],'status':'snapshot-ready' if copied else 'missing','source_root':str(src_root),'snapshot_path':str(dest),'copied_files':copied,'missing_files':missing,'provenance':str(dest/'oss-provenance.json')}


def existing_snapshot_samples(snapshot_base: Path):
    samples=[]
    if not snapshot_base.exists():
        return samples
    for prov in sorted(snapshot_base.glob('*/oss-provenance.json')):
        dest=prov.parent
        data=load(prov,{})
        js_files=[p for p in dest.rglob('*') if p.is_file() and p.suffix.lower() in {'.js','.mjs','.cjs','.jsx','.ts','.tsx'}]
        if not js_files:
            continue
        samples.append({
            'slug':data.get('slug') or dest.name,
            'name':data.get('project') or data.get('name') or dest.name,
            'status':'snapshot-ready',
            'source_root':data.get('source_root','vendored-snapshot'),
            'snapshot_path':str(dest),
            'copied_files':[str(f.relative_to(dest)) for f in js_files[:50]],
            'missing_files':[],
            'provenance':str(prov),
            'source':'existing-vendored-snapshot'
        })
    return samples


def vendor_local_oss10(snapshot_base: Path):
    samples=[]
    seen=set()
    # Prefer existing vendored snapshots on Windows or clean-room hosts where Linux distro paths do not exist.
    for s in existing_snapshot_samples(snapshot_base):
        samples.append(s); seen.add(s.get('slug'))
    for cand in LOCAL_OSS_CANDIDATES:
        s=copy_candidate(cand, snapshot_base)
        if s.get('slug') in seen:
            continue
        if s.get('status')=='snapshot-ready' and any(Path(x).suffix.lower() in {'.js','.mjs','.cjs','.jsx','.ts','.tsx'} for x in s.get('copied_files',[])):
            samples.append(s); seen.add(s.get('slug'))
    return samples


def replay_sample(sample: dict[str,Any], out_root: Path, cwd: Path):
    """Deterministic OSS replay: execute the default TypeScript AST backend on each copied JS file.
    This avoids browser/network work and proves real parser execution against local OSS source snapshots.
    """
    sdir=Path(sample['snapshot_path'])
    sout=out_root/sample['slug']; sout.mkdir(parents=True, exist_ok=True)
    commands=[]; backend_results=[]; files=[]; call_edges=0; source_sink_paths=0; endpoints=0
    js_files=[p for p in sdir.rglob('*') if p.suffix.lower() in {'.js','.mjs','.cjs','.jsx','.ts','.tsx'}]
    node=shutil.which('node') or 'node'
    backend=str((cwd/'scripts/backends/js/typescript_extract.mjs').resolve())
    for jf in js_files[:20]:
        c=run([node, backend, str(jf)], cwd, timeout=20); commands.append(c)
        if c.get('returncode')==0:
            try:
                data=json.loads(c.get('stdout_tail','') if len(c.get('stdout_tail',''))<1900 else subprocess.run([node, backend, str(jf)], cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20).stdout)
            except Exception:
                try: data=json.loads(subprocess.run([node, backend, str(jf)], cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20).stdout)
                except Exception as e: data={'status':'error','error':str(e)}
            data['relative_file']=str(jf.relative_to(sdir))
            backend_results.append(data)
            call_edges += len(data.get('callGraphEdges',[]))
            source_sink_paths += len(data.get('sourceSinkPaths',[]))
            endpoints += len(data.get('endpoints',[]))
            files.append(str(jf.relative_to(sdir)))
    ok=bool(js_files) and bool(backend_results) and all(c.get('returncode')==0 for c in commands if c.get('cmd',[None])[0] != 'skipped')
    graph={'schema_version':'js-semantic-graph/v1','semantic_status':'ready' if ok else 'partial','static_only':True,'no_confirmed_without_runtime':True,'coverage':{'files':len(files),'call_graph_edges':call_edges,'source_sink_paths':source_sink_paths,'endpoints':endpoints},'nodes':[],'edges':[],'evidence':[],'call_graph':[{'file':r.get('relative_file'), **x} for r in backend_results for x in r.get('callGraphEdges',[])[:200]],'source_sink_paths':[{'file':r.get('relative_file'), **x} for r in backend_results for x in r.get('sourceSinkPaths',[])[:200]],'backend_results':backend_results[:20]}
    (sout/'js_semantic_graph.json').write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding='utf-8')
    ledger={'schema_version':'js-top-tier-asset-ledger/v1','root':str(sdir),'assets':[{'path':f,'kind':'javascript'} for f in files],'stats':{'javascript_assets':len(files),'sourcemaps':0,'manifests':0,'service_workers':0,'evidence_items':0}}
    (sout/'js_asset_ledger.json').write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding='utf-8')
    return {'slug':sample['slug'],'name':sample['name'],'status':'ready' if ok else 'failed','snapshot_path':str(sdir),'output_dir':str(sout),'commands':commands,'coverage':{'assets':len(files),'js_assets':len(files),'semantic_status':graph['semantic_status'],'files':len(files),'call_graph_edges':call_edges,'source_sink_paths':source_sink_paths,'endpoints':endpoints}}


def main():
    ap=argparse.ArgumentParser(description='Execute static replay against real local OSS source snapshots. Dynamic browser replay is separate and must not be inferred from static OSS replay.')
    ap.add_argument('--source', default='/opt/novnc')
    ap.add_argument('--snapshot', default='fixtures/oss-replay/real-novnc-snapshot')
    ap.add_argument('--snapshot-base', default='fixtures/oss-replay/real-local-oss10')
    ap.add_argument('--out', default='reports/js-top-tier/real-oss-replay')
    ap.add_argument('--vendor-snapshot', action='store_true')
    ap.add_argument('--vendor-local-oss10', action='store_true')
    ap.add_argument('--attempt-playwright', action='store_true')
    args=ap.parse_args(); out=Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=True); cwd=Path.cwd()
    samples=[]; errors=[]; commands=[]; outputs={}
    if args.vendor_local_oss10:
        samples=vendor_local_oss10(Path(args.snapshot_base).resolve())
    else:
        # compatibility: preserve old noVNC path but now through local-oss vendor if possible.
        base=Path(args.snapshot).resolve().parent
        samples=vendor_local_oss10(base)[:1]
    replay_results=[]
    for sample in samples:
        replay_results.append(replay_sample(sample, out/'samples', cwd))
    ready_count=sum(1 for r in replay_results if r['status']=='ready')
    status='ready' if ready_count>=10 else ('partial' if ready_count else 'missing')
    if args.attempt_playwright:
        errors.append('Browser runtime replay for OSS samples is not executed by this static replay script; use js_playwright_safe_replay_executor.py against an authorized target or local OSS server.')
    result={'schema_version':'js-real-oss-replay-result/v1','status':status,'project':{'mode':'local-oss-multi-sample','required_count':10,'ready_count':ready_count},'commands':commands,'outputs':outputs,'samples':replay_results,'real_oss_replay_count':ready_count,'runtime_replay_status':'not-attempted','promotion_rule':'Ten local OSS static replays prove parser/collector execution on real local OSS source trees. They do not prove dynamic browser validation or vulnerability confirmation.','errors':errors}
    (out/'js_real_oss_replay_result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    registry={'schema_version':'js-oss-replay-registry/v1','status':'ready' if ready_count>=10 else 'needs-import','real_oss_replay_count':ready_count,'samples':[{'name':r['slug'],'description':r['name'],'path':r['snapshot_path'],'status':r['status'],'real_oss_replay':r['status']=='ready','manifest':str(Path(r['snapshot_path'])/'oss-provenance.json')} for r in replay_results],'downgrade':'These are local installed OSS source snapshots, not external live web targets. Runtime validation still requires HAR/trace/screenshot/request-response artifacts.'}
    (out.parent/'js_oss_replay_registry.json').write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':ready_count>=10,'status':status,'real_oss_replay_count':ready_count,'out':str(out/'js_real_oss_replay_result.json')}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ready_count>=10 else 1)
if __name__=='__main__': main()
