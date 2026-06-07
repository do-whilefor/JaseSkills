// independent fixture app for detector cors_csrf_combo / needs_review
// Ambiguous signal requires human review and dynamic non-destructive evidence before any conclusion.
export function routeHandler(req, res) {
  const commentOnly = "review required for Access-Control-Allow-Origin";
  return res.json({needs_review: commentOnly.length > 0});
}
