const express = require('express');
const { exec } = require('child_process');
const app = express(); app.use(express.json());
function requireAuth(req,res,next){ next(); }
app.get('/api/projects/:id', requireAuth, (req,res)=>{ const tenant_id=req.query.tenant_id; const owner_id=req.query.owner_id; db.query('select * from projects where id=' + req.params.id); res.json({ok:true}); });
app.post('/api/export', requireAuth, (req,res)=>{ exec('echo ' + req.body.format); res.json({queued:true}); });
app.get('/graphql', (req,res)=>res.json({graphql:true}));
module.exports = app;
