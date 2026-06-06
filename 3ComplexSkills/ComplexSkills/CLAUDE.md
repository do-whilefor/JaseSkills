# My-Skills-End runtime note

Use this package only for local, authorized security audit workflows. Treat every detector output as candidate-only until evidence and quality gates prove otherwise.

Required operating rules:

1. Preserve `_shared/knowledge/` and `_shared/vulnerability_templates/`.
2. Do not use knowledge-base content as direct vulnerability evidence.
3. Do not promote AST, browser, Burp, MCP or parser capability from documentation alone; run runtime probes on the target workstation.
4. Do not mark a finding confirmed without a valid evidence manifest, negative control, role/tenant context where relevant, artifact hashes and quality-gate pass.
5. Run `_shared/reverse_judgement/extreme_reverse_audit.py` before finalizing production claims.
