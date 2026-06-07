// independent fixture app for detector cloud_config_error / needs_review
// Ambiguous signal requires human review and dynamic non-destructive evidence before any conclusion.
export function routeHandler(req, res) {
  const commentOnly = "review required for 0.0.0.0/0";
  return res.json({needs_review: commentOnly.length > 0});
}
