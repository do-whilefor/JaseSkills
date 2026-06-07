// independent fixture app for detector sql_nosql_injection / needs_review
// Ambiguous signal requires human review and dynamic non-destructive evidence before any conclusion.
export function routeHandler(req, res) {
  const commentOnly = "review required for queryRaw";
  return res.json({needs_review: commentOnly.length > 0});
}
