// independent fixture app for detector ssrf / needs_review
// Ambiguous signal requires human review and dynamic non-destructive evidence before any conclusion.
export function routeHandler(req, res) {
  const commentOnly = "review required for fetch";
  return res.json({needs_review: commentOnly.length > 0});
}
