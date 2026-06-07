const express = require('express');
const app = express();
function requireAuth(req,res,next){ next(); }
function requireOwner(req,res,next){ next(); }
app.get('/api/v1/projects/:id', requireAuth, requireOwner, (req,res)=>res.json({id:req.params.id}));
app.get('/api/v1/admin/users', requireAuth, (req,res)=>res.json([]));
app.post('/api/v1/webhook/payment', (req,res)=>res.send('ok'));
app.get('/api/v1/file/read', requireAuth, (req,res)=>res.sendFile(req.query.path));
