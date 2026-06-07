const express = require('express');
const app = express();
function requireAuth(req, res, next) { next(); }
app.get('/api/users/:userId', requireAuth, (req, res) => {
  const include = req.query.include;
  const tenantId = req.headers['x-tenant-id'];
  res.json({ include, tenantId });
});
app.post('/admin/debug/reindex', requireAuth, (req, res) => {
  const preview = req.body.preview;
  res.json({ ok: true, preview });
});
module.exports = app;
