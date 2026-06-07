// independent fixture app for detector payment_points_coupon_logic / negative
export function routeHandler(req, res) {
  const validatedInput = String((req.body && req.body.value) || '').replace(/[^a-z0-9_-]/gi, '');
  return res.json({ok: true, value: validatedInput});
}
