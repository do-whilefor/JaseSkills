# AI Lazy Loading and Browser Interaction Reverse Audit Checklist v1

Use this checklist before any final vulnerability claim or Skills capability score.

## Execution status labels

Every phase must be marked exactly one of:

- `executed`
- `partially_executed`
- `not_executed`
- `blocked`
- `inferred`
- `evidence_missing`

## Failure conditions

Mark the run failed or blocked when any condition is true:

1. no concrete file path;
2. no code location;
3. no browser interaction matrix;
4. no HAR/network evidence for a dynamic claim;
5. no lazy chunk/source map/service worker/router/API-client scan;
6. no role/tenant matrix for authorization-sensitive findings;
7. no negative test;
8. no variant expansion;
9. no evidence manifest;
10. candidate written as confirmed;
11. static-only audit written as dynamic validation;
12. process omitted scripts, Markdown, config, CI/CD or build output.

## Required self-questions

- Which conclusions were executed and which were inferred?
- Which files, routes, chunks, APIs, roles and tenants were not covered?
- Which browser interactions were skipped and why?
- Which candidate risks could be high-impact false negatives?
- Which candidates could be false positives?
- Which findings require human review?
- Which runtime tools were missing and what did that block?
- What is the next highest-value replay to run?
