// independent fixture app for detector api_version_shadow_endpoint / needs_review
// Ambiguous signal requires human review and dynamic non-destructive evidence before any conclusion.
export function routeHandler(req, res) {
  const commentOnly = "review required for /v1/";
  return res.json({needs_review: commentOnly.length > 0});
}
