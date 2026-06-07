const express = require('express');
const fs = require('fs');
const app = express();
function requireAuth(req,res,next){ next(); }
app.get('/api/orders/:id', requireAuth, (req,res)=>{
  const id = req.params.id;
  const order = db.orders.findById(id); // no owner/tenant check
  res.json(order);
});
app.get('/api/export', requireAuth, (req,res)=>{ fs.readFile(req.query.path, 'utf8', (e,d)=>res.send(d)); });
