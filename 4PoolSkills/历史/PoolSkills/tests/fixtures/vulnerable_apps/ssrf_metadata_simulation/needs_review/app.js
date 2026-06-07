// independent fixture app for detector ssrf_metadata_simulation / needs_review
// Ambiguous signal requires human review and dynamic non-destructive evidence before any conclusion.
export function routeHandler(req, res) {
  const commentOnly = "review required for 169.254.169.254";
  return res.json({needs_review: commentOnly.length > 0});
}
