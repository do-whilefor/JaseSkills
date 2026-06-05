#!/usr/bin/env node
/* Contract-only/non-destructive WebSocket capture scaffold for authorized local targets. */
import fs from 'fs';
function parseArgs(argv){ const a={url:null,out:'ws-capture.json',contractOnly:false}; for(let i=2;i<argv.length;i++){ if(argv[i]==='--url') a.url=argv[++i]; else if(argv[i]==='--out') a.out=argv[++i]; else if(argv[i]==='--contract-only') a.contractOnly=true; } if(!a.url){console.error('usage: node scripts/ws-readonly-capture.mjs --url ws://127.0.0.1:3000/socket --out ws.json [--contract-only]'); process.exit(2);} return a; }
function isLocal(u){ try{ const h=new URL(u).hostname; return ['localhost','127.0.0.1','::1'].includes(h); }catch(_){ return false; } }
const args=parseArgs(process.argv);
if(!isLocal(args.url) && !args.contractOnly){ console.error('refusing non-local websocket without explicit contract-only mode'); process.exit(3); }
const out={schema_version:'ws-readonly-capture.v1', url:String(args.url).split('?')[0], mode: args.contractOnly?'contract_only':'capture_requested', safety:'no messages sent unless configured; no mutation; no auth bypass', frames:[], warnings:[]};
if(args.contractOnly) out.warnings.push('contract_only_no_network_capture');
fs.writeFileSync(args.out, JSON.stringify(out,null,2));
console.error(`wrote ${args.out}`);
