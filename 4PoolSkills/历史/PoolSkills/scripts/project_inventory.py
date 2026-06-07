#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,re,hashlib
from pathlib import Path
SKIP={'.git','node_modules','vendor','target','dist','build','.next','coverage','outputs'}
EXT={'.js':'JavaScript','.ts':'TypeScript','.tsx':'TypeScript','.jsx':'JavaScript','.py':'Python','.java':'Java','.php':'PHP','.rb':'Ruby','.go':'Go','.rs':'Rust','.vue':'Vue','.html':'HTML','.proto':'Proto'}
DEPENDENCY_FILES=['package.json','package-lock.json','yarn.lock','pnpm-lock.yaml','requirements.txt','pyproject.toml','poetry.lock','Pipfile','pom.xml','build.gradle','composer.json','composer.lock','go.mod','go.sum','Cargo.toml','Cargo.lock','Gemfile','Gemfile.lock']
CONFIG_FILES=['Dockerfile','docker-compose.yml','docker-compose.yaml','kubernetes.yml','k8s.yml','.env','.env.example','next.config.js','vite.config.js','webpack.config.js','nuxt.config.js','settings.py','application.yml','application.properties','config.yml','config.yaml']
CI_FILES=['.github/workflows','gitlab-ci.yml','.gitlab-ci.yml','Jenkinsfile','azure-pipelines.yml','circle.yml']
SENSITIVE_RX=[('env_secret',r'(?i)(secret|token|api[_-]?key|private[_-]?key|password)\s*[=:]'),('cloud_cred',r'(?i)(aws_access_key_id|aws_secret_access_key|firebase|supabase|sentry_dsn|dsn\s*[=:])'),('private_key',r'-----BEGIN [A-Z ]*PRIVATE KEY-----')]
FRAMEWORK_SIG={'Express':'express','Next.js':'next','NestJS':'@nestjs','Django':'django','FastAPI':'fastapi','Spring':'springframework','Laravel':'laravel','Rails':'rails','React':'react','Vue':'vue','Angular':'@angular','Gin':'gin-gonic','Fiber':'gofiber','Axum':'axum','Actix':'actix'}
ENTRY_SIG={'upload':['upload','multer','multipart','formidable'],'import_export':['import','export','csv','xlsx','report'],'preview_convert':['preview','convert','thumbnail','imagemagick','libreoffice'],'template':['template','render','jinja','twig','freemarker','velocity'],'webhook':['webhook','signature'],'queue':['queue','worker','consumer','bullmq','celery','sidekiq'],'cron':['cron','schedule','@scheduled'],'plugin':['plugin','extension','loader','loadplugin','postinstall','preinstall','build.rs'],'graphql':['graphql','schema','resolver','subscription'],'grpc':['.proto','grpc'],'rpc':['rpc','trpc','jsonrpc','xmlrpc'],'electron_extension_miniapp':['contextbridge','ipcrenderer','chrome.runtime','browser.runtime','manifest_version','wx.request','my.request','tt.request'],'mobile_legacy_api':['mobile','legacy','compat','v1/','oldapi']}

def sha(p):
    try: return hashlib.sha256(p.read_bytes()).hexdigest()[:16]
    except Exception: return None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('project'); ap.add_argument('--out',default='outputs/asset_ledger.json'); a=ap.parse_args(); root=Path(a.project).resolve()
    files=[]; langs={}; deps=[]; configs=[]; ci=[]; secrets=[]; db=[]; roles=[]; entrypoints=[]; snippets=[]
    for p in root.rglob('*'):
        if any(part in SKIP for part in p.parts) or not p.is_file(): continue
        rel=str(p.relative_to(root)); lowrel=rel.lower(); suf=p.suffix.lower(); files.append({'path':rel,'suffix':suf,'size':p.stat().st_size,'sha256_16':sha(p)})
        if suf in EXT: langs[EXT[suf]]=langs.get(EXT[suf],0)+1
        if p.name in DEPENDENCY_FILES: deps.append({'file':rel,'kind':'dependency_or_lock'})
        if p.name in CONFIG_FILES or any(x in lowrel for x in ['dockerfile','kubernetes','k8s','helm','config/']): configs.append({'file':rel,'kind':'config_or_deployment'})
        if any(x in lowrel for x in CI_FILES): ci.append({'file':rel,'kind':'ci_cd'})
        if any(x in lowrel for x in ['migration','migrations','seed','seeder','factory','fixture']): db.append({'file':rel,'kind':'migration_seed_fixture'})
        try: txt=p.read_text(encoding='utf-8', errors='ignore')[:200000]
        except Exception: txt=''
        low=txt.lower()+"\n"+lowrel
        for name,rx in SENSITIVE_RX:
            if re.search(rx, txt): secrets.append({'file':rel,'type':name,'handling':'redact_value_and_review_authorized_scope'})
        if re.search(r'(?i)(role|permission|tenant|organization|owner|admin|rbac|abac)', low): roles.append({'file':rel,'signals':[x for x in ['role','permission','tenant','organization','owner','admin','rbac','abac'] if x in low]})
        for kind,words in ENTRY_SIG.items():
            hits=[x for x in words if x in low]
            if hits: entrypoints.append({'file':rel,'kind':kind,'signals':hits})
        if len(snippets)<200 and txt: snippets.append(txt[:2000])
    text='\n'.join(snippets).lower()
    frameworks=[fw for fw,s in FRAMEWORK_SIG.items() if s.lower() in text]
    ledger={'schema_version':'asset-ledger-v2','root':str(root),'file_count':len(files),'languages':langs,'frameworks':frameworks,'dependencies':deps,'configs':configs,'ci_cd':ci,'sensitive_material_signals':secrets,'database_models_migrations_seeds':db,'roles_tenants_permissions_signals':roles,'high_risk_entrypoint_signals':entrypoints,'files_sampled':files[:5000],'policy':'inventory only; secrets are signals and must be redacted; do not exfiltrate values or scan third-party targets'}
    Path(a.out).parent.mkdir(parents=True,exist_ok=True); Path(a.out).write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(ledger,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
