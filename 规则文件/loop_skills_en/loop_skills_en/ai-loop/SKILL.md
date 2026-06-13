---

name: anti-hallucination-loop
description: Reduce AI hallucinations during authorized security testing by requiring evidence-driven, stateful judgment, loop-based evidence supplementation, and a ban on fabricated conclusions.
-------------------------------------------------------

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
→ Find verifiable evidence
→ Perform non-destructive validation
→ Compare the baseline and the variant
→ Eliminate false positives
→ Update the status
```

The status can only be:

```text
hypothesis      hypothesis
needs_review    insufficient evidence
rejected        excluded
confirmed       confirmed
reportable      reportable
```

It is prohibited to directly upgrade the following to `confirmed` or `reportable`:

```text
Scanner alerts
500 errors
Frontend prompts
Source maps
Dependency CVEs
Abnormal responses
Static guesses
Model inferences
```

## Evidence Sources

Each piece of evidence must be marked with a source:

```text
observed              actually observed
copied_from_file      read from a file
copied_from_tool      copied from tool output
user_provided         provided by the user
inferred              inferred by the model
missing               missing
```

Only the following sources can support conclusions:

```text
observed
copied_from_file
copied_from_tool
user_provided
```

`inferred` can only be used to propose hypotheses and cannot be used to prove vulnerabilities.

`missing` must be supplemented with evidence and cannot be forced into a conclusion.

## No Fabrication

It is prohibited to fabricate or invent:

```text
File paths
Line numbers
Function names
API endpoints
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
An observable difference exists
Non-destructive validation has been performed
False positives have been eliminated
A real impact explanation exists
```

Before entering `reportable`, it must satisfy:

```text
Within the authorized scope
Non-destructive
Successfully reproduced at least twice
At least one failed case or boundary case exists
Raw request / response / log / code evidence exists
Can explain the affected identity, permission, data, tenant, server-side behavior, or business state
```

## Hallucination Interception

When any of the following occurs, stop upgrading and change the status to `needs_review`:

```text
The evidence chain is broken
Only speculation exists without validation
Only tool alerts exist without manual review
Only a phenomenon exists without impact
Cannot be reproduced
Cannot confirm whether it is within the authorized scope
Cannot confirm whether it is non-destructive
```

When a previous judgment is found to be wrong, record:

```text
Original judgment
Reason for the error
New evidence
Corrected status
```

## Output Requirements

The final output must distinguish:

```text
Confirmed facts
Evidence sources
Model inferences
Missing evidence
Next validation steps
Current status
```

The report must not use vague conclusions:

```text
A high-risk issue may exist
Account takeover is suspected
Privilege bypass should be possible
Large-scale leakage is highly likely
It looks vulnerable
```

Unless they are explicitly marked afterward as:

```text
claim_level: hypothesis
```

Final discipline:

```text
Evidence first, conclusions second.
Insufficient evidence means no upgrade.
Cannot reproduce means do not report.
Tool alerts do not equal vulnerabilities.
Model inferences do not equal facts.
```
