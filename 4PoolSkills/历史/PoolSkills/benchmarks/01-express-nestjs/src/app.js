const express=require('express'); const app=express();
function requireAuth(req,res,next){ if(!req.user) return res.status(401).end(); next(); }
function sameTenant(req,res,next){ if(req.user.tenant !== req.params.tenant) return res.status(403).end(); next(); }
app.get('/api/projects/:id', requireAuth, sameTenant, (req,res)=>res.json({id:req.params.id}));
app.get('/api/admin/users', requireAuth, function requireAdmin(req,res,next){ if(!req.user?.admin) return res.status(403).end(); next();}, (req,res)=>res.json([]));
