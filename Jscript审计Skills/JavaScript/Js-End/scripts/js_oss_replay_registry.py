#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
SAMPLES=[
 ('nextjs-dashboard','Next.js route/chunk/sourcemap/API route sample'),('nuxt-admin','Nuxt payload/i18n/route-meta sample'),('express-api','Express REST/controller/DTO sample'),('nestjs-graphql','NestJS GraphQL resolver sample'),('react-vite-spa','Vite/React dynamic import and feature flag sample'),('vue-router-rbac','Vue router meta role gating sample'),('django-rest','Django/DRF serializer hidden field sample'),('fastapi-openapi','FastAPI OpenAPI schema alignment sample'),('laravel-inertia','Laravel routes/controller/request sample'),('spring-boot','Spring controller/DTO/method-security sample'),('go-chi-api','Go router/model sample'),('rust-axum-api','Rust Axum route/extractor sample')]

def main():
    ap=argparse.ArgumentParser(description='Create real OSS replay registry scaffold. It records import requirements and refuses to mark samples bundled unless source is present.')
    ap.add_argument('--samples-root', default='fixtures/oss-replay')
    ap.add_argument('--out', default='reports/js-top-tier')
    args=ap.parse_args(); sr=Path(args.samples_root); out=Path(args.out); out.mkdir(parents=True, exist_ok=True); sr.mkdir(parents=True, exist_ok=True)
    entries=[]
    for name,desc in SAMPLES:
        d=sr/name; d.mkdir(parents=True, exist_ok=True)
        manifest=d/'replay-manifest.json'
        if not manifest.exists():
            manifest.write_text(json.dumps({'schema_version':'oss-replay-sample/v1','name':name,'description':desc,'status':'needs-import','source_repository':'fill with authorized local clone or OSS URL before replay','license_review_required':True,'commands':{'setup':'fill in','start':'fill in','collect':'python scripts/js_top_tier_collect.py --root <app> --out <out>','replay':'python scripts/js_playwright_safe_replay_executor.py --plan <plan> --execute --out <out>'},'expected_cases':['positive','negative','blocked','needs_review'],'promotion_rule':'not bundled and not real_oss_replay until source tree, license note, replay output, evidence manifest, and quality gate result are present'}, ensure_ascii=False, indent=2), encoding='utf-8')
        m=json.loads(manifest.read_text(encoding='utf-8'))
        present=any((d/x).exists() for x in ['src','app','package.json','pyproject.toml','pom.xml','go.mod','Cargo.toml'])
        entries.append({'name':name,'description':desc,'path':str(d),'status':'bundled-source-present' if present else m.get('status','needs-import'),'real_oss_replay': bool(present and (d/'last-evidence-manifest.json').exists()),'manifest':str(manifest)})
    real=sum(1 for e in entries if e['real_oss_replay'])
    res={'schema_version':'js-oss-replay-registry/v1','status':'ready' if real>=10 else 'needs-import','real_oss_replay_count':real,'samples':entries,'downgrade':'Sample registry is not the same as real OSS replay. Each sample must include source, license note, start command, replay artifacts, and evidence manifest.'}
    (out/'js_oss_replay_registry.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ok':True,'status':res['status'],'real_oss_replay_count':real,'samples':len(entries),'out':str(out/'js_oss_replay_registry.json')}, ensure_ascii=False, indent=2))
if __name__=='__main__': main()
