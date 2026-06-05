# Human Review Queue Policy

Items must enter human review when parser runtime is missing, output was produced by regex/AST-lite fallback, a finding is not DYNAMIC_CONFIRMED, role/tenant/object owner is unresolved, evidence lacks source/request/response/negative control/replay/scope, detector signals conflict with framework behavior, or the result relies on knowledge-base text, README statements, comments, or tool alerts without independent evidence.

Review output must record candidate id, reason, missing evidence, reviewer decision, allowed next action, and whether the report section may be generated.
