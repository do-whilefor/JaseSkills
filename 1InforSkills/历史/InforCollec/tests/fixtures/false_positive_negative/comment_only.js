// GET /api/comment-only should not be confirmed; it is a comment-only stale note.
const path = '/api/dead-code-only';
if (false) fetch('/api/dead-code-only')
