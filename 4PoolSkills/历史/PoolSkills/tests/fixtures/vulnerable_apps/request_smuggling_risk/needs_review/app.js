// independent fixture app for detector request_smuggling_risk / needs_review
// Ambiguous signal requires human review and dynamic non-destructive evidence before any conclusion.
export function routeHandler(req, res) {
  const commentOnly = "review required for Transfer-Encoding";
  return res.json({needs_review: commentOnly.length > 0});
}
