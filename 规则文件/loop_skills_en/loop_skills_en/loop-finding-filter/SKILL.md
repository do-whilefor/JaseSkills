---

name: loop-finding-filter
description: Filter out invalid, low-risk, theoretical, and scanner-alert-type findings, allowing only issues with real impact and sufficient evidence to enter reports.
------------------------------------------------------

# Loop Finding Filter

## Core Principles

A vulnerability is not a “phenomenon”; a vulnerability must prove real impact.

By default, ignore issues that cannot affect the following boundaries:

```text
Identity
Authentication
Authorization
Permissions
User boundaries
Tenant boundaries
Sensitive data
Server-side boundaries
File boundaries
Execution boundaries
Core business state
```

For every round of judgment, ask yourself:

```text
Is this only an abnormal phenomenon, or has it already caused a result?
Has it crossed a real security boundary?
Is there reproducible evidence?
Would a security team recognize this as a vulnerability?
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
Ordinary 500 errors
Ordinary Debug information
Open Redirect
Missing rate limits
Self-XSS
Weak XSS signals
Single scanner alerts
Frontend bypasses
Public information exposure
Username / email enumeration
Weak password policies
TLS / SPF / DKIM / DMARC best-practice issues
Ordinary low-sensitivity information leakage with quantity < 5000
```

These issues may only be upgraded when they form a real attack chain and the impact is proven.

## Upgrade Conditions

Low-value phenomena may be reported only when they directly lead to the following results:

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
SQL / template / command / object injection with real impact
Abuse of payments / refunds / balances / coupons / orders / approvals / withdrawals
Identity-binding bypass
```

Do not report without proving the attack chain and impact.

## Information Leakage Rules

Information leakage must distinguish between “ordinary low-sensitivity information” and “high-impact sensitive information.”

Ordinary low-sensitivity information leakage is not reported by default. It may enter `confirmed` or `reportable` only when the following conditions are met:

```text
Leakage quantity >= 5000 records
Can prove the data comes from a non-public API, unauthorized API, privilege-bypass API, or cross-tenant API
Can prove the data is genuinely accessible, rather than frontend cache, a public page, test data, or a scanner false positive
Can prove the leaked content has real impact on users, business, permissions, assets, or security boundaries
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
Business numbers with no sensitive meaning
List data that cannot be associated with real identity or account risk
```

The following information is not subject to the `5000 records` quantity limit. As long as it is proven to be non-public, accessible, reproducible, and to have real impact, it may be upgraded:

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
Enterprise internal sensitive data
Cross-user sensitive data
Cross-tenant sensitive data
```

Final judgment rules:

```text
Ordinary low-sensitivity information leakage: quantity must be >= 5000 to enter confirmed / reportable
Sensitive credential leakage: not subject to the 5000 records limit
Token / Cookie / AKSK / password / private key: not subject to the 5000 records limit
Cross-user / cross-tenant sensitive data: not subject to the 5000 records limit
Unauthorized access to sensitive data: not subject to the 5000 records limit
Public low-sensitivity information: rejected by default
Cannot prove non-public: rejected by default
Cannot prove real impact: needs_review or rejected by default
```

It is prohibited to use high-frequency crawling, bulk scraping, brute-force enumeration, or expanded access scope to make up the quantity.

If quantity needs to be proven, only use non-destructive, low-frequency methods within the authorized scope, such as:

```text
The total field returned by an API
The count field in paginated responses
Backend statistics fields
Test-environment database statistics
Authorized sample statistics in logs
A small number of samples + explicit server-side total-volume evidence
```

Do not infer large-scale leakage merely because a small number of samples are seen. Quantity conclusions must come from actual evidence.

## Fast Rejection Rules

Reject CORS unless:

```text
It has been proven that the attacker origin can read sensitive credentialed responses
```

Reject CSRF unless:

```text
A sensitive server-side state change has been completed, such as a password, email, OAuth, payment, order, or permission change
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
They leak keys, credentials, Tokens, SQL context, sensitive file content, or lead to real impact such as authentication bypass, SSRF, injection, or file read
```

Reject Open Redirect unless:

```text
It affects OAuth, SSO, Tokens, trusted-domain bypass, or login-flow security
```

Reject rate-limit issues unless:

```text
OTP brute forcing, password brute forcing, SMS / email bombing, or business abuse involving coupons, invitations, refunds, orders, balances, and similar functions is proven
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
→ False-positive elimination
→ confirmed
```

Without manual reproduction, it must not enter the report.

## 7 Questions Before Reporting

Before writing the final report, all of the following must pass:

```text
1. Is there a PoC, curl, raw request, or executable proof?
2. Is the report about actual impact rather than a mere phenomenon?
3. Has it been reproduced at least twice?
4. Has a failed or boundary case been performed?
5. Is it within the authorized scope and non-destructive?
6. Have common false positives been eliminated?
7. Is the impact on confidentiality, integrity, availability, identity, permissions, tenants, server-side behavior, or business state clear?
```

If any item fails:

```text
Do not report
Mark rejected or needs_review
Record the missing evidence
Switch to a higher-value hypothesis
```

## Output Rules

The final report can only contain:

```text
Confirmed impact
Attacker capability
Affected boundary
Raw evidence
Reproduction steps
False-positive elimination
Security or business consequences
Remediation recommendations
```

Final judgment:

```text
Real impact + reproducible evidence + authorized scope + non-destructive = reportable
Otherwise = rejected or needs_review
```
