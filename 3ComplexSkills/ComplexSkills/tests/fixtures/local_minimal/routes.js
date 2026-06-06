const express = require('express');
const app = express();
app.get('/api/users/:id', userHandler);
app.post('/admin/export', adminExportHandler);
app.delete('/api/projects/:projectId', deleteProjectHandler);
