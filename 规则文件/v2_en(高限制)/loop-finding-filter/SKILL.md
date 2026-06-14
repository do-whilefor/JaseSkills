---
name: loop-finding-filter
description: Filters invalid, low-risk, theoretical, and scanner-alert-type vulnerabilities, allowing only issues with real impact and sufficient evidence into reports.
---

# Loop Finding Filter

## Core Principles

A vulnerability is not a "phenomenon"; a vulnerability must prove real impact.

By default, ignore issues that cannot affect the following boundaries:

```text
Identity
Authentication
Authorization
Permissions
User boundary
Tenant boundary
Sensitive data
Server-side boundary
File boundary
Execution boundary
Core business state
```

Ask yourself in every round of judgment:

```text
Is this only an abnormal phenomenon, or has it already caused a result?
Has it crossed a real security boundary?
Is there reproducible evidence?
Would the security team recognize this as a vulnerability?
```

If the answer is no, mark it as:

```text
rejected / needs_review
```

Do not write it into the final report.

## Default Do-Not-Report List

The following issues are not reported by default:

```text
CORS
CSRF
Missing security response headers
Clickjacking
Version number / Banner leakage
Ordinary 500 error
Ordinary Debug information
Open Redirect
Missing rate limiting
Self-XSS
Weak XSS signal
Single-point scanner alert
Frontend bypass
Public information exposure
Username / email enumeration
Weak password policy
TLS / SPF / DKIM / DMARC best-practice issues
Ordinary low-sensitivity information leakage with quantity < 5000
```

These issues may only be upgraded when they form a real attack chain and prove impact.

## Upgrade Conditions

Low-value phenomena are only reportable when they directly lead to the following results:

```text
Account takeover
Authentication bypass
Authorization bypass
Privilege escalation
Cross-user data access
Cross-tenant data access
Sensitive data leakage
Token / credential leakage
SSRF with proof that the server initiated the request
Arbitrary file read
Arbitrary file write
Server-side code or command execution
SQL / template / command / object injection with actual impact
Payment / refund / balance / coupon / order / approval / withdrawal abuse
Identity-binding bypass
```

Do not report without proving the attack chain and impact.

## Information Leakage Rules

Information leakage must distinguish between "ordinary low-sensitivity information" and "high-impact sensitive information".

Ordinary low-sensitivity information leakage is not reported by default and may enter `confirmed` or `reportable` only when all of the following conditions are met:

```text
Leakage quantity >= 5000 records
Able to prove the data comes from a non-public API, unauthorized API, privilege-escalation API, or cross-tenant API
Able to prove the data is truly accessible, rather than frontend cache, a public page, test data, or a scanner false positive
Able to prove the leaked content has actual impact on users, business, permissions, assets, or security boundaries
```

Ordinary low-sensitivity information includes:

```text
Usernames
Nicknames
Avatars
Ordinary user IDs
Ordinary display fields
Public profiles
Public organization names
Business numbers without sensitive meaning
List data that cannot be associated with real identity or account risk
```

The following information is not subject to the `5000 records` quantity limit. As long as it is proven to be non-public, accessible, reproducible, and to have real impact, it can be upgraded:

```text
Tokens
Cookies
Sessions
AKSK
Passwords
Private keys
API Keys
Verification codes
Password reset links
Login-state credentials
Backend credentials
Cloud service credentials
Database connection strings
Identity credentials that can take over accounts
Medical information
Financial information
Internal enterprise sensitive data
Cross-user sensitive data
Cross-tenant sensitive data
```

Final judgment rules:

```text
Ordinary low-sensitivity information leakage: quantity must be >= 5000 to enter confirmed / reportable
Sensitive credential leakage: not subject to the 5000-record limit
Token / Cookie / AKSK / password / private key: not subject to the 5000-record limit
Cross-user / cross-tenant sensitive data: not subject to the 5000-record limit
Unauthorized access to sensitive data: not subject to the 5000-record limit
Public low-sensitivity information: rejected by default
Unable to prove non-public status: rejected by default
Unable to prove real impact: needs_review or rejected by default
```

Do not perform high-frequency collection, bulk crawling, brute-force enumeration, or scope expansion just to reach a quantity threshold.

If quantity must be proven, only use non-destructive, low-frequency, in-scope methods, for example:

```text
The total field returned by an API
The count field in a paginated response
Backend statistics fields
Test-environment database statistics
Authorized sample statistics in logs
A small number of samples + explicit server-side total evidence
```

Do not infer large-scale leakage merely from seeing a small number of samples. Quantity conclusions must come from actual evidence.

## Quick Rejection Rules

Reject CORS unless:

```text
It has been proven that an attacker origin can read sensitive responses carrying credentials
```

Reject CSRF unless:

```text
A sensitive server-side state change has been completed, such as password, email, OAuth, payment, order, or permission changes
```

Reject missing security headers unless:

```text
They are part of a verified high-impact attack chain
```

Reject Clickjacking unless:

```text
It can complete a sensitive operation and cause real impact
```

Reject version leakage unless:

```text
The leaked version corresponds to a high-impact vulnerability, and the current target has been proven affected
```

Reject ordinary errors unless:

```text
They leak keys, credentials, Tokens, SQL context, sensitive file contents, or lead to real impacts such as authentication bypass, SSRF, injection, or file read
```

Reject Open Redirect unless:

```text
It affects OAuth, SSO, Tokens, trusted-domain bypass, or login-flow security
```

Reject rate-limit issues unless:

```text
They prove business abuse such as OTP brute forcing, password brute forcing, SMS / email bombing, coupons, invitations, refunds, orders, or balances
```

Reject XSS unless:

```text
It executes in a real browser and affects other users, administrators, sensitive data, account state, or business actions
```

Reject frontend bypass unless:

```text
The backend accepted an unauthorized action or state change
```

Reject public information exposure unless:

```text
It exposes keys, private data, credentials, sensitive personal information, or exploitable internal sensitive information
```

Reject ordinary low-sensitivity information leakage unless:

```text
Leakage quantity >= 5000, and it is proven to be non-public, reproducible, and to have real impact
```

## Scanner Rules

Scanner output is only a lead, not a vulnerability.

It must go through:

```text
Tool alert
→ Request / source-code review
→ Reachability check
→ Manual reproduction
→ Impact proof
→ False-positive exclusion
→ confirmed
```

Without manual reproduction, it does not enter the report.

## 7 Questions Before Reporting

Before writing the final report, all of the following must pass:

```text
1. Is there a PoC, curl, raw request, or executable proof?
2. Is the report about actual impact rather than a mere phenomenon?
3. Has it been reproduced at least twice?
4. Has a failed or boundary case been tested?
5. Is it within authorized scope and non-destructive?
6. Have common false positives been excluded?
7. Is the impact on confidentiality, integrity, availability, identity, permissions, tenants, server-side behavior, or business state clearly stated?
```

If any item does not pass:

```text
Do not report
Mark rejected or needs_review
Record missing evidence
Switch to a higher-value hypothesis
```

## Output Rules

Final reports may only contain:

```text
Confirmed impact
Attacker capability
Affected boundary
Raw evidence
Reproduction steps
False-positive exclusion
Security or business consequences
Fix recommendations
```

Final judgment:

```text
Real impact + reproducible evidence + authorized scope + non-destructive = reportable
Otherwise = rejected or needs_review
```

---

## Vulnerability Impact and Severity-Inflation Reflection

When outputting any candidate vulnerability, confirmed vulnerability, or final report vulnerability, each vulnerability entry must include "impact and severity review", and must proactively reflect on whether the vulnerability's impact is large enough and whether the current severity is inflated.

The following must be checked item by item:

```text
1. Whether the real impact is large enough: whether it truly affects identity, authentication, authorization, permissions, tenant boundaries, sensitive data, server-side behavior, file boundaries, execution boundaries, or core business state.
2. Whether the severity is inflated: whether the current rating is based only on theoretical possibility, scanner alerts, abnormal symptoms, best-practice gaps, unverified attack chains, or model inference.
3. Whether the impact scope is supported by evidence: whether the affected user count, data volume, permission span, business consequences, reproduction conditions, and attack prerequisites all have evidence.
4. Whether downgrade or rejection reasons exist: frontend-only behavior, low-sensitivity information only, high-privilege prerequisite, strong user interaction required, unstable reproduction, inability to cross a security boundary, insufficient evidence.
5. Whether the final severity needs adjustment: keep, downgrade, upgrade, or convert to needs_review / rejected.
```

Each vulnerability entry must contain the following fields:

```yaml
severity_reflection:
  impact_large_enough: true|false|unknown
  rating_maybe_inflated: true|false|unknown
  evidence_supports_impact: true|false
  downgrade_or_reject_reasons:
    - "<reason>"
  final_severity_after_reflection: critical|high|medium|low|info|needs_review|rejected
  rationale: "<Use evidence to explain why this severity is not overstated and is not underestimated>"
```

If `evidence_supports_impact=false`, the vulnerability must not be output as `confirmed` or `reportable`.

If it cannot be proven that a real security boundary was crossed, it must be downgraded to `needs_review` or `rejected`.

If the vulnerability severity mainly comes from guesses, tool alerts, abnormal responses, or theoretical attack chains, the severity-inflation risk must be explicitly stated, and downgrade should be prioritized.
