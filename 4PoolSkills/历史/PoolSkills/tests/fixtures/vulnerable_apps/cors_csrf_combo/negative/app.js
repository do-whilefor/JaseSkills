// independent fixture app for detector cors_csrf_combo / negative
export function routeHandler(req, res) {
  const validatedInput = String((req.body && req.body.value) || '').replace(/[^a-z0-9_-]/gi, '');
  return res.json({ok: true, value: validatedInput});
}
