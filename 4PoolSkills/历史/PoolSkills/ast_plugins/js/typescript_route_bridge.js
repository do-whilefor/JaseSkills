#!/usr/bin/env node
const fs = require('fs');
function fail(msg){ console.log(JSON.stringify({status:'missing', plugin:'typescript_compiler', error:msg, nodes:[], edges:[]})); process.exit(0); }
let ts; try { ts = require('typescript'); } catch(e){ fail('missing typescript module: '+e.message); }
const file = process.argv[2]; if (!file || !fs.existsSync(file)) fail('missing input file');
const source = ts.createSourceFile(file, fs.readFileSync(file,'utf8'), ts.ScriptTarget.Latest, true);
const nodes=[]; const edges=[];
function addNode(type,id,props={}){ nodes.push({id,type,file,...props}); return id; }
function text(n){ return n && n.getText(source); }
function walk(n){

  if (ts.isFunctionDeclaration(n) && n.name && /^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)$/.test(n.name.getText(source))){
    const method=n.name.getText(source); const route=file.replace(/.*(?:app\/api|pages\/api)/,'').replace(/\/route\.(t|j)sx?$/,'').replace(/\.(t|j)sx?$/,'') || '/';
    const rid=addNode('route',`${file}:${method} ${route}`,{method,route,framework:'next_route_handler'});
    const hid=addNode('handler',`${file}:${method}:${n.pos}`,{name:method}); edges.push({from:rid,to:hid,type:'ROUTE_TO_HANDLER'});
  }
  if (ts.isMethodDeclaration(n) && n.decorators){
    const decs=Array.from(n.decorators).map(d=>text(d));
    const rd=decs.find(s=>/@(Get|Post|Put|Patch|Delete|All)\s*\(/.test(s));
    if(rd){
      const m=rd.match(/@(Get|Post|Put|Patch|Delete|All)\s*\(([^)]*)\)/);
      const method=(m?m[1]:'ALL').toUpperCase(); const route=(m&&m[2]||'').replace(/["'`]/g,'').trim()||'/';
      const h=String(n.name.getText(source)); const rid=addNode('route',`${file}:${method} ${route}`,{method,route,framework:'nestjs'});
      const hid=addNode('handler',`${file}:${h}`,{name:h}); edges.push({from:rid,to:hid,type:'ROUTE_TO_HANDLER'});
      decs.forEach(ds=>{ if(/UseGuards|AuthGuard|Roles|Permissions/.test(ds)){ const mid=addNode('middleware',`${file}:${h}:guard`,{name:ds}); edges.push({from:rid,to:mid,type:'USES_MIDDLEWARE'}); edges.push({from:mid,to:addNode('authn',`${file}:${h}:authn`,{}),type:'ENFORCES_AUTHN'}); }});
    }
  }
  ts.forEachChild(n, walk);
}
walk(source);
console.log(JSON.stringify({status:'ready', plugin:'typescript_compiler', file, nodes, edges}, null, 2));
