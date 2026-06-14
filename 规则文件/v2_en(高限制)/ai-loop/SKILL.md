---
name: anti-hallucination-loop
description: Reduces AI hallucination during authorized security testing by requiring evidence-driven conclusions, stateful judgment, loop-based evidence supplementation, and prohibiting fabricated conclusions.
---

# Anti Hallucination Loop

## Core Principles

Do not treat guesses as facts, do not treat anomalies as vulnerabilities, and do not treat tool alerts as conclusions.

All conclusions must come from evidence. When there is no evidence, they can only be marked as hypotheses or pending confirmation.

## Loop Process

Each round must follow this process:

```text
Observe the phenomenon
→ Mark the evidence source
→ Propose a hypothesis
→ Look for verifiable evidence
→ Perform non-destructive validation
→ Compare baseline and variant
→ Eliminate false positives
→ Update state
```

States can only be:

```text
hypothesis      Hypothesis
needs_review    Insufficient evidence
rejected        Excluded
confirmed       Confirmed
reportable      Reportable
```

Do not directly upgrade the following to `confirmed` or `reportable`:

```text
Scanner alerts
500 errors
Frontend prompts
Source Maps
Dependency CVEs
Abnormal responses
Static guesses
Model inferences
```

## Evidence Sources

Each piece of evidence must be labeled with its source:

```text
observed              Actually observed
copied_from_file      Read from a file
copied_from_tool      Copied from tool output
user_provided         Provided by the user
inferred              Model inference
missing               Missing
```

Only the following sources can support conclusions:

```text
observed
copied_from_file
copied_from_tool
user_provided
```

`inferred` can only be used to propose hypotheses and cannot be used to prove vulnerabilities.

`missing` must have evidence supplemented and cannot be forced into a conclusion.

## Prohibit Fabrication

Do not fabricate or invent:

```text
File paths
Line numbers
Function names
API addresses
Request parameters
Response content
Status codes
Cookies
Tokens
Logs
Screenshots
Tool output
Reproduction counts
Impact scope
Fix results
```

When uncertain, explicitly write:

```yaml
evidence_status: missing
claim_level: hypothesis
cannot_claim_as_vulnerability: true
```

## Review Rules

Before a vulnerability is upgraded, it must at least satisfy:

```text
Baseline evidence exists
Variant evidence exists
Observable difference exists
Non-destructive validation exists
False-positive exclusion exists
Real impact explanation exists
```

Before entering `reportable`, it must satisfy:

```text
Within authorized scope
Non-destructive
At least two successful reproductions
At least one failed or boundary case
Raw request / response / log / code evidence exists
Able to explain impact on identity, permissions, data, tenants, server-side behavior, or business state
```

## Hallucination Interception

When any of the following occurs, stop upgrading and change the state to `needs_review`:

```text
Evidence chain is broken
Only speculation without validation
Only tool alerts without manual review
Only a phenomenon without impact
Cannot reproduce
Cannot confirm whether it is within authorized scope
Cannot confirm whether it is non-destructive
```

When a previous judgment is found to be wrong, record:

```text
Original judgment
Reason for error
New evidence
Corrected state
```

## Output Requirements

Final output must distinguish:

```text
Confirmed facts
Evidence sources
Model inferences
Missing evidence
Next validation steps
Current state
```

Do not use vague conclusions in reports:

```text
Potential high-risk issue may exist
Suspected account takeover is possible
Privilege escalation should be possible
High probability of leakage
Looks like a vulnerability
```

Unless clearly marked afterward as:

```text
claim_level: hypothesis
```

Final discipline:

```text
Evidence first, conclusion second.
Insufficient evidence, no upgrade.
Cannot reproduce, do not report.
Tool alerts do not equal vulnerabilities.
Model inferences do not equal facts.
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
