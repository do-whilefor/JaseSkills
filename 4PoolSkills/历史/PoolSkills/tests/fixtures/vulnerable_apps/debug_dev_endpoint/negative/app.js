// independent fixture app for detector debug_dev_endpoint / negative
export function routeHandler(req, res) {
  const validatedInput = String((req.body && req.body.value) || '').replace(/[^a-z0-9_-]/gi, '');
  return res.json({ok: true, value: validatedInput});
}
