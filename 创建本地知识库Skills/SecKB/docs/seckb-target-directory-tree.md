# SecKB 目标目录结构

```text
D:\Users\21452\AppData\SecKB
├── CLAUDE.md
├── README.md
├── indexes
│   ├── master-index.json
│   ├── source-index.json
│   ├── cve-index.json
│   ├── src-rules-index.json
│   ├── tool-release-index.json
│   └── template-index.json
├── sources
│   ├── official-advisories
│   ├── cve-nvd-kev
│   ├── github-security-advisories
│   ├── vendor-advisories
│   ├── src-platform-rules
│   ├── bug-bounty-reports
│   ├── tool-docs-releases
│   └── research-blogs
├── vulns
│   ├── web
│   ├── authz-idor
│   ├── auth-session-token
│   ├── ssrf
│   ├── rce
│   ├── injection
│   ├── file-upload-file-read
│   ├── deserialization
│   ├── xss-csrf
│   ├── business-logic
│   ├── cloud-ci-cd-supply-chain
│   └── frontend-js
├── code-audit
│   ├── javascript-typescript
│   ├── python
│   ├── java
│   ├── php
│   ├── go
│   ├── ruby
│   ├── rust
│   ├── dotnet
│   └── mobile-extension-electron
├── templates
│   ├── vuln-templates
│   ├── report-templates
│   ├── dynamic-validation-templates
│   ├── false-positive-checklists
│   └── cannot-report-reasons
├── src-rules
│   ├── domestic
│   ├── international
│   └── normalized
├── toolchain
│   ├── releases
│   ├── readme-digests
│   ├── command-templates
│   └── integration-notes
├── labs
│   ├── reproducible-cves
│   ├── patch-diff
│   ├── local-targets
│   └── notes
├── evidence
│   ├── manifests
│   ├── request-response
│   ├── screenshots
│   ├── code-snippets
│   └── reproduction-logs
├── review
│   ├── needs-human-confirmation
│   ├── conflicts
│   ├── stale-items
│   ├── rejected
│   └── promoted
└── scripts
    ├── update_sources.ps1
    ├── normalize_records.py
    ├── dedupe_records.py
    ├── score_sources.py
    ├── build_indexes.py
    ├── check_freshness.py
    └── quality_gate.py
```
