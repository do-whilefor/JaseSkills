# Blackboard

> Only record tested parts, results, evidence, review decisions, and next steps. Update at the end of each round.

```yaml
scope:
  targets: []
  identities: []
  note: ""

tested:
  # - id: T001
  #   object: "API / page / JS / parameter / business function"
  #   identity: "unauthenticated / userA / userB / admin / test account"
  #   method: "How it was tested, preferably in one sentence"
  #   result: "success / failure / no anomaly / weak signal / reproducible"
  #   evidence_path: "evidence/..."
  #   status: untested|tested|candidate|verified|rejected|blocked

findings:
  # - id: F001
  #   object: ""
  #   summary: "Confirmed or pending issue"
  #   evidence_path: "evidence/..."
  #   status: candidate|verified|rejected|blocked
  #   next: "continue verification / write report / abandon"

metacog:
  # - id: M001
  #   target: "T001/F001/object"
  #   kill: "Fatal gap or downgrade reason"
  #   survive: "Evidence-backed reason to continue"
  #   anti_evidence: "Observable negative case or counter-evidence"
  #   branch: "Next controllable verification step"
  #   decision: continue|branch|downgrade|reject|block
  #   evidence_path: "evidence/..."

guardian:
  # - id: G001
  #   target: "F001/object"
  #   issue: "garbage finding / broken chain / inflated rating / acceptable"
  #   decision: accept|downgrade|reject|block
  #   reason: "Why this decision was made"
  #   evidence_path: "evidence/..."

blocked:
  # - id: B001
  #   object: ""
  #   reason: "Why it is blocked"
  #   need: "What is needed to continue"

next:
  priority: ""
  object: ""
  action: ""
  reason: ""
```