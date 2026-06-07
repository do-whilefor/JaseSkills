// independent fixture app for detector api_version_shadow_endpoint / negative
export function routeHandler(req, res) {
  const validatedInput = String((req.body && req.body.value) || '').replace(/[^a-z0-9_-]/gi, '');
  return res.json({ok: true, value: validatedInput});
}
