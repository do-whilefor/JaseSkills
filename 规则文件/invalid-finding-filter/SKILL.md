# Invalid Finding Filter

## Purpose

This skill prevents the AI from reporting low-value, weak, theoretical, or non-impactful security findings.

The AI must not treat every error, warning, scanner alert, configuration issue, or abnormal response as a vulnerability.

This skill is a report filter. It decides what should be ignored by default.

---

## Core Rule

Do not report findings that do not create real security impact.

A finding should be ignored unless it proves impact on at least one of:

* unauthorized access
* authorization bypass
* authentication bypass
* privilege escalation
* account takeover
* cross-user access
* cross-tenant access
* sensitive data leakage
* SSRF with proven server-side request
* arbitrary file read or write
* server-side execution
* injection with real impact
* high-impact business logic abuse

If the finding does not affect identity, permission, sensitive data, server-side boundary, tenant boundary, or core business state, do not report it.

---

## Default Ignore List

The following issues must not be reported by default.

Only record them as ignored notes if necessary.

### 1. CORS

Do not report CORS issues by default.

Ignore when:

* no credentials are allowed
* no sensitive data can be read
* browser cannot read the response
* only public APIs are affected
* only static resources are affected
* there is no working proof of sensitive cross-origin data access

Report only if CORS directly causes credentialed sensitive data leakage or account-impacting behavior.

---

### 2. CSRF

Do not report CSRF issues by default.

Ignore when:

* action is not sensitive
* action only changes theme, language, search, logout, or preferences
* action requires user confirmation
* SameSite, Origin, Referer, or CSRF token protection is effective
* no meaningful server-side state change is proven

Report only if CSRF causes sensitive state change, such as password change, email binding, OAuth binding, payment, refund, permission change, order operation, or account takeover chain.

---

### 3. Missing Security Headers

Do not report missing headers by default.

Ignore standalone issues involving:

* CSP
* HSTS
* X-Frame-Options
* X-Content-Type-Options
* Referrer-Policy
* Permissions-Policy
* Cache-Control
* Secure cookie flag
* HttpOnly cookie flag
* SameSite cookie flag

Report only if the missing header is part of a proven high-impact exploit chain.

---

### 4. Clickjacking

Do not report clickjacking by default.

Ignore when:

* only homepage or marketing page can be framed
* no sensitive action can be completed
* user confirmation is still required
* no real business or account impact exists

Report only if clickjacking completes a sensitive action with real impact.

---

### 5. Version or Banner Disclosure

Do not report version, framework, server, or banner disclosure by default.

Ignore:

* server header
* framework name
* version number
* technology fingerprint
* build timestamp
* public dependency name

Report only if the disclosed version maps to a high-impact vulnerability and the current target is proven affected.

---

### 6. Generic Error or 500 Response

Do not report ordinary errors by default.

Ignore:

* generic HTTP 500
* empty error page
* error ID only
* generic exception text
* malformed request causing crash-like response without impact
* response difference without exploitability

Report only if the error leaks secrets, sensitive data, exploitable stack details, SQL context, credentials, tokens, or leads to confirmed injection, file read, auth bypass, or SSRF.

---

### 7. Ordinary Debug Information

Do not report debug information by default.

Ignore:

* non-sensitive debug text
* ordinary file paths
* route names
* public API names
* framework traces without secrets
* harmless configuration names

Report only if debug output exposes credentials, tokens, secrets, internal sensitive data, or a direct exploit path.

---

### 8. Open Redirect

Do not report open redirect by default.

Ignore simple redirects without security chain.

Report only if it enables:

* OAuth token leakage
* SSO bypass
* account takeover
* trusted-domain bypass
* login flow abuse
* sensitive authentication chain impact

---

### 9. Rate Limit Weakness

Do not report missing rate limit by default.

Ignore when:

* endpoint is harmless
* no abuse impact is proven
* only manual repeated requests are shown
* no account, money, resource, or business abuse exists

Report only if it enables OTP brute force, password brute force, SMS bombing, email bombing, coupon abuse, invite abuse, refund abuse, order abuse, balance abuse, or other meaningful business abuse.

---

### 10. Self-XSS or Weak XSS Signal

Do not report weak XSS findings by default.

Ignore:

* self-XSS
* payload reflected but not executed
* payload blocked by CSP
* DOM sink not attacker-reachable
* alert-only finding with no affected user or sensitive context
* markdown rendering quirk without cross-user impact

Report only if XSS executes in a real browser and affects another user, privileged user, sensitive data, account state, or business action.

---

### 11. Scanner-Only Alerts

Do not report scanner alerts by default.

Ignore any scanner finding without manual proof.

Scanner output is only a hint.

A scanner alert must be downgraded unless there is:

* manual reproduction
* raw request and response
* clear attacker control
* real impact
* false-positive check

---

### 12. Frontend-Only Issues

Do not report frontend-only issues by default.

Ignore:

* hidden button visible in frontend
* disabled button re-enabled
* frontend route accessible
* client-side validation bypass
* UI price changed locally
* role name changed in local storage
* JavaScript variable modified locally

Report only if the server accepts the unauthorized action or state change.

---

### 13. Public or Non-Sensitive Information

Do not report public information exposure by default.

Ignore:

* robots.txt
* sitemap.xml
* public JS paths
* public CSS paths
* public image paths
* public documentation
* public GitHub metadata
* ordinary directory names
* non-sensitive static directory listing

Report only if sensitive secrets, private data, credentials, or exploitable internal information is exposed.

---

### 14. Username or Email Enumeration

Do not report enumeration by default.

Ignore standalone:

* username exists / not exists difference
* email exists / not exists difference
* login error wording difference
* registration duplicate message

Report only if it contributes to account takeover, brute force, privacy leakage at scale, or accepted program-specific impact.

---

### 15. Weak Password Policy

Do not report weak password policy by default.

Ignore standalone:

* short password allowed
* no complexity rule
* common password accepted
* no password history

Report only if it directly enables account compromise in the tested flow and the impact is proven.

---

### 16. TLS, SPF, DKIM, DMARC, and Best-Practice Issues

Do not report these by default unless explicitly requested by the user or scope.

Ignore standalone:

* TLS grade issue
* weak cipher observation
* SPF issue
* DKIM issue
* DMARC issue
* email security best practice
* OPTIONS enabled
* TRACE claimed without proven impact

Report only if the program scope asks for configuration review or a real exploit chain is proven.

---

## Upgrade Rule

A default-ignored issue may be reported only if it directly leads to one of the following:

* account takeover
* authentication bypass
* authorization bypass
* privilege escalation
* cross-user data access
* cross-tenant data access
* sensitive data leakage
* token or credential leakage
* SSRF with proven server-side request
* arbitrary file read
* arbitrary file write
* server-side code or command execution
* SQL injection or equivalent injection with impact
* payment, refund, balance, coupon, order, approval, withdrawal, or identity-binding abuse

If none of these are proven, do not report it.

---

## Required Decision

Before reporting any finding, the AI must ask:

1. Is this only a low-value or best-practice issue?
2. Does it cross a real security boundary?
3. Does it affect identity, permission, data, server-side behavior, tenant isolation, or business state?
4. Is there proof beyond a scanner alert or abnormal response?
5. Would a security team accept this as a real vulnerability?

If the answer is no, mark it as ignored and do not include it in the final report.

---

## Output Rule

Final vulnerability reports must exclude:

* CORS without sensitive credentialed read
* CSRF without sensitive state change
* missing headers
* clickjacking without sensitive action
* version or banner disclosure
* generic 500 errors
* ordinary debug info
* open redirect without auth impact
* rate limit issue without abuse impact
* self-XSS
* weak XSS signal
* scanner-only alert
* frontend-only bypass
* public information exposure
* username enumeration alone
* weak password policy alone
* best-practice-only issues

The final report should contain only confirmed, high-impact, evidence-backed vulnerabilities.
