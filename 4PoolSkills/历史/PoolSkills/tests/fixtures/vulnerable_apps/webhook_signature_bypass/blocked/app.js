// independent fixture app for detector webhook_signature_bypass / blocked
export const blockedPayload = "DROP TABLE must be blocked by scope_guard and never sent";
export function routeHandler(req, res) { return res.status(400).json({blocked: true}); }
