const express = require('express'); const app = express();
app.get('/api/tenant/settings', requireAuth, (req, res) => res.json({ok:true}));
