// independent fixture app for detector cicd_leak_abuse / needs_review
// Ambiguous signal requires human review and dynamic non-destructive evidence before any conclusion.
export function routeHandler(req, res) {
  const commentOnly = "review required for GITHUB_TOKEN";
  return res.json({needs_review: commentOnly.length > 0});
}
