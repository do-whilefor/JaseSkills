#!/usr/bin/env node
/*
 * Non-destructive role/tenant matrix HAR contract runner.
 * If Playwright is unavailable or config.contract_only=true, writes a contract artifact
 * instead of pretending runtime capture succeeded.
 */
import fs from 'fs';
import path from 'path';

function parseArgs(argv){
  const a={config:null,out:'role-matrix-out'};
  for(let i=2;i<argv.length;i++){
    if(argv[i]==='--config') a.config=argv[++i];
    else if(argv[i]==='--out') a.out=argv[++i];
  }
  if(!a.config){ console.error('usage: node scripts/playwright-har-role-matrix.mjs --config matrix.json --out outdir'); process.exit(2); }
  return a;
}
function mkdirp(p){ fs.mkdirSync(p,{recursive:true}); }
function loadPlaywright(){ try { return require('playwright'); } catch(_) { return null; } }
function redactUrl(u){ try{ const x=new URL(u); x.search=''; return x.toString(); }catch(_){ return String(u).split('?')[0]; } }
async function main(){
  const args=parseArgs(process.argv); const cfg=JSON.parse(fs.readFileSync(args.config,'utf8'));
  mkdirp(args.out);
  const playwright=loadPlaywright();
  const contractOnly=cfg.contract_only===true || !playwright;
  const roles=cfg.roles || [{name:'anonymous'}];
  const tenants=cfg.tenants || [{name:'default'}];
  const urls=cfg.urls || [];
  const runId='role-matrix-'+Date.now();
  const evidence={schema_version:'runtime-evidence.v1', run_id:runId, mode: contractOnly?'contract_only':'playwright_capture', playwright_available:!!playwright, scope_id:cfg.scope_id||'local-authorized', records:[]};
  for(const role of roles){
    for(const tenant of tenants){
      for(const url of urls){
        evidence.records.push({role_context:role.name, tenant_context:tenant.name, url:redactUrl(url), method:'GET', capture_status:contractOnly?'planned_not_captured':'pending_capture', request_sample:null, response_sample:null, screenshot:null, har_entry:null, safety:'non_destructive_readonly'});
      }
    }
  }
  fs.writeFileSync(path.join(args.out,'runtime-evidence.json'), JSON.stringify(evidence,null,2));
  fs.writeFileSync(path.join(args.out,'README.txt'), contractOnly ? 'Contract-only artifact: Playwright unavailable or contract_only=true. Do not treat as dynamic proof.\n' : 'Runtime capture scaffold created.\n');
  console.error(`wrote role matrix runtime evidence: ${path.join(args.out,'runtime-evidence.json')}`);
}
main().catch(e=>{ console.error(e.stack||String(e)); process.exit(1); });
