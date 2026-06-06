#!/usr/bin/env node
import { createHash } from 'crypto';
import fs from 'fs';
function usage(){ console.error('Usage: node browser-storage-collect-playwright.mjs --url URL --out out.json [--label role] [--state storageState.json] [--allow-host host] [--headed]'); process.exit(2); }
const args=process.argv.slice(2);
const opts={label:'unauthenticated',allowed:new Set(['localhost','127.0.0.1','0.0.0.0','::1','[::1]']),headed:false};
for(let i=0;i<args.length;i++){ const a=args[i]; if(a==='--url')opts.url=args[++i]; else if(a==='--out')opts.out=args[++i]; else if(a==='--label')opts.label=args[++i]; else if(a==='--state')opts.state=args[++i]; else if(a==='--allow-host')opts.allowed.add(args[++i]); else if(a==='--headed')opts.headed=true; else usage(); }
if(!opts.url||!opts.out) usage();
let base; try{base=new URL(opts.url)}catch{throw new Error('Invalid --url')};
const host=base.hostname;
if(!opts.allowed.has(host)){ throw new Error(`Refusing non-local/non-allowed host: ${host}. Use --allow-host ${host} only for explicitly authorized targets.`); }
function sha256(s){ return createHash('sha256').update(String(s??'')).digest('hex'); }
function redactString(s){
  s=String(s??''); if(!s)return '';
  let out=s.slice(0,240);
  out=out.replace(/(eyJ[A-Za-z0-9_.-]+)/g,m=>m.slice(0,3)+'****'+m.slice(-3));
  out=out.replace(/(sk_[A-Za-z0-9_-]+)/g,m=>m.slice(0,7)+'****'+m.slice(-4));
  out=out.replace(/(token|secret|api[_-]?key|password|session|cookie)=([^&\s]+)/gi,(m,k)=>k+'=****');
  out=out.replace(/([A-Za-z0-9_-]{20,})/g,m=>m.slice(0,4)+'****'+m.slice(-4));
  return out;
}
function summarizeValue(v){ let raw; try{ raw=typeof v==='string'?v:JSON.stringify(v); }catch{ raw=String(v); } return {type:typeof v,length:raw.length,sha256:sha256(raw),redacted_sample:redactString(raw)}; }
function summarizeUrl(raw){
  try{
    const u=new URL(raw, base.href); const sameOrigin=(u.origin===base.origin); const queryKeys=[...u.searchParams.keys()].slice(0,30);
    return {same_origin:sameOrigin, scheme:u.protocol.replace(':',''), host:sameOrigin?u.hostname:`sha256:${sha256(u.hostname).slice(0,16)}`, path:redactString(u.pathname), query_keys:queryKeys, url_sha256:sha256(u.href)};
  }catch{ return {parse_error:true, raw_sha256:sha256(raw), redacted_sample:redactString(raw)}; }
}
function summarizeKey(k){ return {key_redacted:redactString(k), key_sha256:sha256(k)}; }
async function main(){
  let playwright; try{ playwright=await import('playwright'); }catch(e){ console.error('Playwright is not installed. Install only in your authorized environment: npm i -D playwright'); process.exit(3); }
  const browser=await playwright.chromium.launch({headless:!opts.headed});
  const contextOpts={}; if(opts.state) contextOpts.storageState=opts.state;
  const context=await browser.newContext(contextOpts);
  const page=await context.newPage();
  await page.goto(opts.url,{waitUntil:'domcontentloaded',timeout:30000});
  await page.waitForTimeout(1000);
  const cookies=(await context.cookies()).map(c=>({name:c.name,domain:c.domain,path:c.path,httpOnly:c.httpOnly,secure:c.secure,sameSite:c.sameSite,expires:c.expires,value_length:String(c.value??'').length,value_sha256:sha256(c.value??''),redacted_sample:redactString(c.value??'')}));
  const storage=await page.evaluate(async()=>{
    function entriesOf(s){const arr=[]; for(let i=0;i<s.length;i++){const k=s.key(i); arr.push([k,s.getItem(k)]);} return arr;}
    async function inspectIndexedDB(){const result=[]; if(!('indexedDB' in window))return result; if(!indexedDB.databases)return [{note:'indexedDB.databases() not supported by this browser/context'}]; const dbs=await indexedDB.databases(); for(const dbInfo of dbs){const name=dbInfo.name; if(!name)continue; const one={name,version:dbInfo.version,stores:[]}; try{ const db=await new Promise((resolve,reject)=>{const req=indexedDB.open(name); req.onsuccess=()=>resolve(req.result); req.onerror=()=>reject(req.error); req.onblocked=()=>reject(new Error('blocked'));}); for(const storeName of Array.from(db.objectStoreNames)){const tx=db.transaction(storeName,'readonly'); const store=tx.objectStore(storeName); const count=await new Promise(resolve=>{const req=store.count(); req.onsuccess=()=>resolve(req.result); req.onerror=()=>resolve(null);}); const keys=await new Promise(resolve=>{const req=store.getAllKeys(undefined,5); req.onsuccess=()=>resolve(req.result.map(String)); req.onerror=()=>resolve([]);}); one.stores.push({name:storeName,count,key_samples:keys});} db.close();}catch(e){one.error=String(e.message||e);} result.push(one);} return result;}
    async function inspectCaches(){const result=[]; if(!('caches' in window))return result; const names=await caches.keys(); for(const name of names){const cache=await caches.open(name); const reqs=await cache.keys(); result.push({cache:name,requests:reqs.slice(0,100).map(r=>({url:r.url,method:r.method,mode:r.mode,destination:r.destination}))});} return result;}
    async function inspectSW(){ if(!('serviceWorker' in navigator))return []; const regs=await navigator.serviceWorker.getRegistrations(); return regs.map(r=>({scope:r.scope,active:r.active?r.active.scriptURL:null,installing:r.installing?r.installing.scriptURL:null,waiting:r.waiting?r.waiting.scriptURL:null,controller:navigator.serviceWorker.controller?navigator.serviceWorker.controller.scriptURL:null})); }
    return {localStorage:entriesOf(localStorage),sessionStorage:entriesOf(sessionStorage),indexedDB:await inspectIndexedDB(),cacheStorage:await inspectCaches(),serviceWorkers:await inspectSW()};
  });
  const summarizeEntries=arr=>arr.map(([key,value])=>({...summarizeKey(key),...summarizeValue(value)}));
  const indexedDB=(storage.indexedDB||[]).map(db=>({...db, name_redacted:redactString(db.name||''), name_sha256:sha256(db.name||''), stores:(db.stores||[]).map(st=>({...st, name_redacted:redactString(st.name||''), name_sha256:sha256(st.name||''), key_samples:(st.key_samples||[]).map(k=>summarizeKey(String(k)))}))}));
  const cacheStorage=(storage.cacheStorage||[]).map(c=>({cache_redacted:redactString(c.cache), cache_sha256:sha256(c.cache), requests:(c.requests||[]).map(r=>({url_summary:summarizeUrl(r.url),method:r.method,mode:r.mode,destination:r.destination}))}));
  const serviceWorkers=(storage.serviceWorkers||[]).map(sw=>({scope:summarizeUrl(sw.scope),active:sw.active?summarizeUrl(sw.active):null,installing:sw.installing?summarizeUrl(sw.installing):null,waiting:sw.waiting?summarizeUrl(sw.waiting):null,controller:sw.controller?summarizeUrl(sw.controller):null}));
  const output={collected_at:new Date().toISOString(),url_summary:summarizeUrl(opts.url),final_url_summary:summarizeUrl(page.url()),role_label:opts.label,scope_note:'authorized local/project target only; values and URLs are redacted/hashed',cookies,localStorage:summarizeEntries(storage.localStorage||[]),sessionStorage:summarizeEntries(storage.sessionStorage||[]),indexedDB,cacheStorage,serviceWorkers};
  fs.writeFileSync(opts.out,JSON.stringify(output,null,2));
  await browser.close();
}
main().catch(err=>{console.error(err.stack||String(err)); process.exit(1);});
