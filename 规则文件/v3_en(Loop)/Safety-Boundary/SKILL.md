---
name: Safety-Boundary
description: Safety boundaries are execution guardrails, not brakes on thinking; candidates broad, verification steady, reporting strict.
metadata:
  short-description: Safety boundary
---

# Safety Boundary

Goal: ensure testing does not go out of control while not suppressing autonomous AI divergence.

---
## 1. First Principles

```text
User input = the current authorization scope.
Safety boundaries only restrict real actions; they do not restrict candidate generation.
Broad divergence across identities, objects, states, interfaces, JS, files, business flows, credentials, callbacks, cache, and historical data is allowed.
Hidden interfaces, hidden parameters, hidden states, hidden roles, and impact scope may be hypothesized for designing the next verification step.
Hypotheses must be marked as hypothesis; inferences must not be written as verified.
Real execution must be low-risk, minimized, and rollback-capable.
```

---
## 2. Minimum Hard Red Lines

Execution is prohibited for:

```text
Testing assets outside the user-input scope.
Destructive writes, deletion, and batch modification of real data.
DoS, stress testing, high-frequency requests, and resource exhaustion.
Accessing real cloud metadata or non-test data without explicit authorization.
Stealing, exporting, or spreading real user privacy or production-sensitive data.
Persistent backdoors, Trojans, malicious scripts, hidden accounts, and persistence of privileges.
Expanding request intensity or polluting real business operations in order to prove impact.
```
When a hard red line is hit, do not stop thinking; only stop the dangerous execution path and switch to static evidence, logs, local mock, test environment, read-only proof, or downgrade the candidate to `parked`.

---
## 2.1 Detailed Prohibited Items

The following sentences come from more conservative boundary rules and serve as a detailed version of the minimum hard red lines. They only constrain real actions, not security hypotheses, path divergence, or evidence reasoning.

```text
DoS / DDoS / stress testing / high-frequency recursive scanning / infinite request loops / CPU, memory, disk, or queue resource exhaustion / slow requests dragging down the service / bypassing rate limits and causing unavailability / high-concurrency brute force: prohibited.
DROP / TRUNCATE / batch DELETE / batch UPDATE / modifying real business data / emptying tables / destroying indexes, migration records, audit logs, backups, or object storage: prohibited.
Stopping services / restarting services / killing processes / clearing caches, queues, or logs / changing production configuration / affecting Webhooks, scheduled tasks, other users' sessions / triggering real external notifications / modifying real user or merchant materials: prohibited.
CDN or underlying cloud-provider services, cloud metadata, real intranets, wireless networks, MITM, traffic hijacking, certificate replacement, and real accounts not explicitly authorized: testing prohibited.
```

Alternative-path priority: static proof, local mock, dry-run, test accounts, test data, transaction rollback, minimal sentinel records. If safe verification is still impossible, the candidate can only be `parked`.

---
## 3. Low-Risk Verification Priority

```text
1. Static proof from source code, configuration, routes, JS, and logs.
2. Reproduction in local environments, test environments, and mocks.
3. Read-only requests.
4. Object/permission/state comparisons between test accounts.
5. Minimized PoC, avoiding destructive actions.
```

Credential-type verification should only perform minimal read-only proof: whether it is non-public, whether it is valid, its permission scope, and whether it can access sensitive resources. Abusing credentials to expand impact is prohibited.

---
## 4. Stability Check Before Verification

Before any real action, first check:

```text
Are the asset, account, object, and environment within the authorization scope provided by the user?
Is the action read-only, minimized, and rollback-capable?
Will it trigger batch operations, state pollution, real charges, real notifications, real deletion, or real export?
Will it access unauthorized third parties or real user privacy?
Is there a safer alternative: source code, logs, local mock, test environment, or read-only comparison?
```

When the conditions cannot be satisfied, do not continue real verification; downgrade the candidate to `parked` and record the conditions needed for reactivation.

---
## 5. Balancing Sentence

```text
Keep the candidate stage as broad as possible: allow divergence, guessing, combination, mutation, adjacent-surface expansion, and counterfactual reasoning.
The verification stage must be stable: low-risk, read-only first, minimized, rollback-capable.
The reporting stage must be strict: real evidence, two successes, one negative case, severity backpressure, and impact reflection.
```

The role of safety boundaries is to keep the AI from going out of control, not to make the AI think less.
