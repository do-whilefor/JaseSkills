# Knowledge base invocation rules

Knowledge base entries, vulnerability notes and payload notes can only create hypotheses, checklist prompts or template hints.

Hard rules:

1. Knowledge references cannot be used as direct vulnerability evidence.
2. Current project code evidence and local dynamic evidence outrank knowledge base content.
3. Knowledge older than the configured freshness window must set `freshness_reviewed=true`.
4. Conflicting knowledge must move the item to `conflict` or `needs_review`; it cannot be confirmed.
5. Payload notes are never executable instructions for third-party targets.
