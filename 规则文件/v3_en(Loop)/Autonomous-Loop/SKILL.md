---
name: Autonomous-Loop
description: Less is more: let the AI proactively diverge and use a Soft Loop to prevent idle spinning.
metadata:
  short-description: Autonomous SRC loop
---

# Autonomous SRC Soft Loop

Goal: keep the loop running efficiently, allowing the AI to evolve by itself within the authorized circle without drifting off target, idling, or falsely completing.

---
## 1. First Principles

```text
First iron rule: ordinary CORS / security headers / version numbers / Self-XSS / Source Map with no sensitive information / ordinary Open Redirect / single scanner alert = do not submit independently.
User input = the current authorization scope.
Safety boundaries restrict real execution, not candidate generation.
Keep the candidate stage as broad as possible, the verification stage stable, and the reporting stage strict.
Only write boundaries, directions, and standards; let the model choose the testing methods by itself.
```
---
## 2. Quick Reference Card

```text
No PoC / curl / request-response / source-code call chain / logs / screenshot evidence = nonexistent.
Phenomenon != vulnerability; the real result must be proven.
Ordinary CORS / security headers / version numbers / Self-XSS / ordinary Open Redirect / Source Map with no sensitive information / single scanner alert = do not submit independently.
Prioritize authorization bypass, unauthenticated access, IDOR, tenant isolation, privilege escalation, sensitive data, batch/export, file ownership, and core business state.
Rank candidates by ROI: impact boundary × verifiability × authorization safety × clue freshness - destructive risk - evidence gap.
For response fields from interface A, try transplanting them to interface B, filtering, sorting, export, asynchronous results, and file keys.
Sorting parameters sort/order/orderBy, filtering parameters filter/query, and pagination parameters page/limit/cursor are high-value input boundaries.
If two consecutive exploration windows have no effective progress, switch direction.
Before switching direction, after long sessions, and before reporting, reread the quick reference card.
```

---
## 3. Six Axes of Proactive Divergence

Every clue must be proactively expanded; testing only the explicit path is not allowed.

```text
identity: anonymous, ordinary user, creator, collaborator, approver, administrator, service account, third-party callback.
object: own object, others' objects, historical objects, deleted objects, cross-organization objects, cross-tenant objects.
state: draft, pending review, reviewed, canceled, archived, deleted, expired, asynchronous processing, failed retrying.
operation: read, write, delete, export, batch, upload, download, share, approve, callback, replay, asynchronous result reading.
asset: API, JS, Source Map, GraphQL, WebSocket, mobile interface, admin interface, object storage, exported files, logs, cache, queues, Webhook.
chain: authentication, authorization, object ownership, state machine, file ownership, server-side behavior, data scale, sensitive fields, business loss.
```

Divergence output must be layered: `hypothesis_space`, `next_safe_action`, `evidence_space`, `reportable`. Guesses may only enter hypothesis; they must not enter facts, impact, severity, or reports.

---
## 4. Decision-Tree Guidance

```text
Has login functionality -> prioritize authorization bypass / IDOR / role differences / tenant isolation.
Is an API service -> prioritize unauthenticated access / object ownership / parameter transplantation / batch export.
Lots of JS -> extract hidden interfaces, routes, fields, and Source Map clues; do not report the Source Map itself.
Has upload/download/preview -> test file ownership, presigned URLs, transcoding, sharing, expiration, and recycle bin.
Has search/sorting/filtering -> test input boundaries, unauthorized queries, sorting fields, and batch enumeration.
Has GraphQL/WebSocket -> test identity, object, and state validation for query/mutation/message.
Has asynchronous tasks/export/reports -> test submission permissions, result-reading permissions, historical results, and download-key ownership.
Has nothing -> do inventory first, then look for high-ROI entry points from JS, APIs, routes, configuration, logs, and dependencies.
```

The decision tree is not a fixed process. The AI may jump, combine, and backtrack, but it must record why it switched.

---
## 4.1 ROI Ranking

```text
ROI = impact boundary × verifiability × authorization safety × clue freshness - destructive risk - evidence gap.
Test first: candidates with large boundary impact, low-risk verification, real evidence sources, and positive/negative comparisons.
Test later: candidates that rely only on tool alerts, have large evidence gaps, require dangerous actions, or can only prove impact on the user's own account.
```

ROI only determines testing order; it does not determine vulnerability severity.

---
## 5. Soft Loop State

Keep only a small amount of state:

```text
idea: clue, hypothesis, boundary issue.
chain_seed: weak signal, not reportable by itself, but connectable to a high-value boundary.
testing: candidate that can be verified at low risk.
parked: high ROI but lacking accounts, objects, source code, logs, environment, or safety conditions.
rejected: no impact, no boundary breakthrough, unreachable, out of scope, dangerous, or not supported by evidence.
confirmed: evidence supports a real boundary breakthrough, but it still must pass the 7 gates.
```

Do not mechanically delete hypotheses by round. High-value directions that temporarily lack conditions should be parked first; only those disproven or without impact should be rejected.

---
## 6. Idle-Spinning Handling

```text
Effective progress: new fact, new question, new variable, new candidate, new evidence source, new rejection, new downgrade, new combination chain, new blocking reason, new next_safe_action.
Idle spinning: repeating the same interface, parameter, object, tool alert, or weak signal without new evidence, new variables, or new chain value.
Switching: when two consecutive exploration windows idle, or when risk increases, evidence is exhausted, or ROI declines, switch to an adjacent high-value surface.
```

The loop only prevents long-term deadlock or false completion.

---
## 7. Coverage Debt

When testing only one direction for a long time, check whether the following have been missed:

```text
identity / object / state / operation / asset / chain / async / tenant / file / callback
```

Coverage debt is for reminders, not for filling matrices. Do not write tables during ordinary thinking; record only when state changes, evidence is written to disk, direction switches, candidate conclusions are made, or restart handoff occurs.
