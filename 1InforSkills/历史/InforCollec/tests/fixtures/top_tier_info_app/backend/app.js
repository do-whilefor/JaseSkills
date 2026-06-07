const express = require('express'); const app = express();
app.get('/api/v1/users/:id', requireAuth, (req,res)=>res.json({id:req.params.id}));
app.post('/internal/admin/reindex', authorize('admin'), handler);
const wsEvent = socket.on('tenant:billing:update', msg => {});
const FEATURE_BETA_EXPORT = true; // deprecated endpoint /api/old/export token name LEGACY_API_TOKEN
