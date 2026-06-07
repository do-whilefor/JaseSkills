// independent fixture app for detector payment_points_coupon_logic / needs_review
// Ambiguous signal requires human review and dynamic non-destructive evidence before any conclusion.
export function routeHandler(req, res) {
  const commentOnly = "review required for price";
  return res.json({needs_review: commentOnly.length > 0});
}
