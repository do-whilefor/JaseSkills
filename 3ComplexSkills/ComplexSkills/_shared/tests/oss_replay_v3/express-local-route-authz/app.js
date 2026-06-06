const express=require('express'); const app=express(); app.get('/api/projects/:id',(req,res)=>res.json({id:req.params.id}));
