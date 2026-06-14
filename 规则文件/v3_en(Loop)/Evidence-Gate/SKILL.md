---
name: Evidence-Gate
summary: Phenomena are not vulnerabilities; only conclusions supported by evidence may enter reports, with mandatory severity backpressure.
---

# Evidence Quality Gate

This skill only reviews candidate upgrades and report conclusions; it does not suppress divergence. The AI may boldly guess interfaces, parameters, object relationships, and impact paths; however, reports may only contain content that the evidence_space can prove.

First iron rule: never package ordinary CORS, security headers, version numbers, Self-XSS, Source Map with no sensitive information, ordinary Open Redirect, single scanner alerts, or missing best practices as independent vulnerabilities.

---
## 1. Never Submit Independently

The following default to `rejected` and must not be used as vulnerability titles, vulnerability types, or independent report conclusions:

```text
Ordinary CORS.
Ordinary CSRF.
Missing security response headers.
Clickjacking.
Version numbers / Banner / technology-stack disclosure.
Ordinary 500 / ordinary Debug / ordinary error stack.
Ordinary Open Redirect.
Self-XSS.
Weak XSS signal / only alert / no sensitive impact.
Single scanner alert.
Source Map with no sensitive information.
Unreachable dependency CVE.
Front-end bypass but effective backend.
Public information / robots / sitemap.
Ordinary directory listing with no sensitive files.
OPTIONS/TRACE enabled but with no actual impact.
Ordinary partial enumeration of usernames/emails/phone numbers with no batch/authentication risk.
Missing rate limiting with no actual impact.
Missing TLS/SPF/DKIM/DMARC/HSTS and other best practices with no provable attack path.
Exposure of non-sensitive paths, buckets, CDNs, environment names, or appids.
Ordinary low-sensitivity information disclosure < 5000.
Only affects the user's own account, with no privilege escalation, no sensitive data, and no state-level authorization bypass.
```

Hitting the list does not mean deletion. If it can enter an authentication, authorization, credential, file, OAuth/SSO, state-change, cross-origin sensitive-read, or server-side behavior chain, downgrade it to `chain_seed`; if conditions are missing but ROI exists, downgrade it to `parked`.

---
## 2. Phenomena and Results

```text
Phenomena: configuration abnormalities, missing response headers, interface existence, errors, versions, front-end display, tool alerts.
Results: data leakage, privilege escalation, unauthorized access, unauthenticated operations, file-ownership breakthrough, core-state bypass, server-side controllable behavior, business loss.
```

Before reporting, you must answer: am I reporting a phenomenon, or a result? Report only results.

---
## 3. Real Evidence

Acceptable evidence:

```text
Code, configuration, request packets, response packets, logs, screenshots, compressed packages, and documents uploaded or pasted by the user.
Real packet-capture requests and responses.
Real source-code snippets and call chains.
Real JS, routes, Source Maps, and dependency lists.
Real raw tool output.
Real files written to disk, with paths that can be opened and contents that can be traced.
```

Not acceptable as original evidence: AI reasoning summaries, AI report drafts, paths that cannot be opened, files whose source cannot be located, fabricated requests/responses, accounts, object IDs, data volumes, tenant counts, or affected user counts.

---
## 4. Claim-Evidence Binding

Every claim must bind to evidence:

```text
claim: the conclusion to prove.
evidence_refs: real requests, responses, logs, source code, screenshots, JS, tool output, or file paths.
observed_fact: the fact directly shown by the evidence.
verified_part: the part already verified.
hypothesis: unverified hypotheses, which may only be parked/needs_more_evidence.
```

The claim must not exceed the evidence. After removing the vulnerability name, the evidence must still prove the impact. Tool alerts must have reachability, manual reproduction, or equivalent source-code proof.

---
## 5. The 7 Gates Before Reporting

If any one fails, it must not be reportable.

```text
1. Is there a reproducible PoC / curl / request-response / executable command / equivalent source-code proof?
2. Is the report about a phenomenon, or about an already proven real security result?
3. Are there two successful reproductions, or equivalent proof covering different accounts/objects/states/request conditions?
4. Is there at least one negative/boundary case proving the normal boundary fails?
5. Have ordinary CORS, security headers, version numbers, Self-XSS, ordinary Open Redirect, scanner false positives, and other invalid items been excluded?
6. Has cross-interface parameter transplantation been tried: feeding field A to interface B, export, sorting, asynchronous result, or file key?
7. Is the impact assessment specific, and are confidentiality/integrity/availability all less than or equal to the evidence?
```

For source-code audits, equivalent proof may replace dynamic reproduction, but it must include the call chain, permission boundary, controllable input, dangerous sink, impact path, and counterexample conditions.

---
## 5.1 Adversarial Review Gate Before Reporting

Before a formal report, first reject the report on behalf of the reviewer:

```text
List the 3 most likely reasons for rejection.
Each reason must be refuted one by one using evidence_refs.
Claims that cannot be refuted must be deleted, downgraded, or changed to needs_more_evidence / parked.
Do not use "possibly, probably, theoretically" to refute rejection reasons.
```

Only after adversarial review passes may the finding enter reportable.

---
## 6. Anti-Hallucination Backpressure

```text
If no actual enumeration was performed, do not write "batch".
If a second account was not covered, do not write "any user".
If a second tenant was not covered, do not write "cross-tenant".
If high-privilege resources were not verified, do not write "administrator privileges".
If sensitive fields were not verified, do not write "sensitive data leakage".
If write operations were not verified, do not write "tampering is possible".
If stability was not verified, do not write "stable reproduction".
If validity and permission scope were not verified, do not write "valid credentials".
"Possibly/suspected/theoretically/usually/probably" may only enter hypothesis/parked, not confirmed/reportable.
```

---
## 7. Severity Ceiling

```text
Tool alerts / version numbers / missing best practices -> rejected/P4.
Single response difference, no negative case, no second object -> parked/P3 ceiling.
Only affects the user's own account -> P4/rejected.
Small amount of low-sensitivity data from others -> P3/P2 ceiling.
Small amount of sensitive data from others -> P2 ceiling.
Batch sensitive data + authorization bypass/unauthenticated access -> P1 ceiling.
Cross-tenant sensitive data -> P1/P0 depending on scale and business impact.
Valid high-privilege credentials, RCE, arbitrary file write, core system control -> P0/P1.
```

The output must include: `claimed_severity`, `evidence_based_severity`, `downgrade_reason`. When the claimed severity is higher than the evidence-based severity, it must be downgraded.

---
## 8. Impact Reflection

Before preparing something as reportable, ask yourself:

```text
Does it really break a permission, object, state, file, tenant, server-side behavior, or sensitive-data boundary?
Are the attacker's prerequisites realistic and supported by evidence?
Are the affected objects, data volume, account count, and tenant count based on evidence rather than inference?
Is this merely low-sensitivity information, missing best practices, a front-end phenomenon, a tool alert, or impact on only the user's own account?
Are there server-side secondary validation, one-time tokens, expiration restrictions, permission convergence, audit blocking, or business compensation controls?
If the vulnerability title is removed and only evidence_refs are examined, does the severity still hold?
```

The conclusion can only be: `reportable`, `needs_more_evidence`, `downgraded`, `parked`, `rejected`. When uncertain, downgrade or park.
