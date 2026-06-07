# Blocked and human review policy

This file records gating rules for items that cannot be promoted by documentation, user confirmation, or package metadata alone.

## Runtime readiness

- AST backends, Playwright, browsers, Burp, MCP and external parser bridges must be probed on the target workstation before they are treated as ready.
- A tool is `ready` only when its runtime probe succeeds. Missing, degraded, or manually configured tools remain `runtime_blocked` or `manual_required`.
- User confirmation can add context, but it does not override `_shared/tools/tool_health_check.py`, `tools/runtime_check.py`, parser runtime probes, or Playwright launch checks.

## Project context

- Without a local project path, startup command, allowed hosts, test accounts, test tenants and safe test data, vulnerability candidates remain `validation_blocked` or `needs_human_review`.
- Without an evidence manifest, findings remain observations or candidates, not confirmed vulnerabilities.

## Unsafe operations

Destructive writes, data deletion, denial-of-service, large-scale load tests, unauthorized third-party probing, credential abuse, persistence and real data exfiltration are out of scope.
