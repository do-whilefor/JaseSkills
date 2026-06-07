// independent fixture app for detector electron_extension_service_worker / needs_review
// Ambiguous signal requires human review and dynamic non-destructive evidence before any conclusion.
export function routeHandler(req, res) {
  const commentOnly = "review required for contextBridge";
  return res.json({needs_review: commentOnly.length > 0});
}
