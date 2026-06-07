# Supabase Security Audit Workspace

This directory is configured for professional Supabase security auditing with strict logging requirements.

## Mandatory Logging Protocol

**CRITICAL**: Every action MUST be logged. This is non-negotiable for audit compliance.

### Files to Maintain

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `.sb-pentest-context.json` | Shared context between skills | After EVERY skill execution |
| `.sb-pentest-audit.log` | Detailed action log with timestamps | After EVERY action |
| `.sb-pentest-evidence/` | Professional evidence collection | After EVERY finding |

### Logging Requirements

1. **Before ANY action**: Log intent to `.sb-pentest-audit.log`
2. **After ANY action**: Log result to `.sb-pentest-audit.log`
3. **After ANY finding**: Update `.sb-pentest-context.json` AND save evidence
4. **For P0/P1/P2 findings**: Update `timeline.md` in evidence directory

### Log Entry Format

```
[YYYY-MM-DD HH:MM:SS] [SKILL_NAME] [ACTION_TYPE] Description
[YYYY-MM-DD HH:MM:SS] [SKILL_NAME] [RESULT] Finding or outcome
```

Example:
```
[2024-01-15 14:32:01] [supabase-detect] [START] Scanning https://example.com for Supabase usage
[2024-01-15 14:32:03] [supabase-detect] [RESULT] Supabase detected - Project URL: xxx.supabase.co
```

## Audit Execution Rules

### Rule 1: Always Use Plan Mode
Before starting the audit, enter Plan Mode to design the approach:
```
Use EnterPlanMode to plan the audit strategy
```

### Rule 2: Initialize Evidence Collection First
Before any testing, run:
```
/supabase-evidence
```

### Rule 3: Execute ALL 24 Skills Systematically

**MANDATORY**: You MUST execute ALL skills in order. No exceptions.

#### Phase 1: Orchestration & Evidence Setup
- [ ] `/supabase-evidence` - Initialize evidence collection (RUN FIRST)

#### Phase 2: Detection
- [ ] `/supabase-detect` - Detect Supabase usage

#### Phase 3: Key Extraction (ALL 5 skills)
- [ ] `/supabase-extract-url` - Extract project URL
- [ ] `/supabase-extract-anon-key` - Extract anon key
- [ ] `/supabase-extract-service-key` - Check for leaked service key (CRITICAL)
- [ ] `/supabase-extract-jwt` - Extract and decode JWTs
- [ ] `/supabase-extract-db-string` - Check for exposed DB strings (CRITICAL)

#### Phase 4: API Audit (ALL 4 skills)
- [ ] `/supabase-audit-tables-list` - List exposed tables
- [ ] `/supabase-audit-tables-read` - Test data access
- [ ] `/supabase-audit-rls` - Test RLS policies
- [ ] `/supabase-audit-rpc` - Test RPC functions

#### Phase 5: Storage Audit (ALL 3 skills)
- [ ] `/supabase-audit-buckets-list` - List storage buckets
- [ ] `/supabase-audit-buckets-read` - Test bucket access
- [ ] `/supabase-audit-buckets-public` - Check public bucket exposure

#### Phase 6: Auth Audit (ALL 4 skills)
- [ ] `/supabase-audit-auth-config` - Analyze auth configuration
- [ ] `/supabase-audit-auth-signup` - Test signup restrictions
- [ ] `/supabase-audit-auth-users` - Test user enumeration
- [ ] `/supabase-audit-authenticated` - Test authenticated access & IDOR

#### Phase 7: Realtime & Functions (ALL 2 skills)
- [ ] `/supabase-audit-realtime` - Test Realtime channels
- [ ] `/supabase-audit-functions` - Test Edge Functions

#### Phase 8: Reporting (ALL 2 skills)
- [ ] `/supabase-report` - Generate comprehensive report
- [ ] `/supabase-report-compare` - Compare with previous audits (if applicable)

**TOTAL: 24 skills must be executed for a complete audit.**

### Rule 4: Never Skip Phases
- Do NOT skip any phase without explicit user confirmation
- Log skipped phases with reason in audit log

### Rule 5: Update Context After Each Skill
After EVERY skill execution, update `.sb-pentest-context.json`:
```json
{
  "lastUpdated": "ISO_TIMESTAMP",
  "currentPhase": "PHASE_NAME",
  "completedSkills": ["skill1", "skill2"],
  "findings": {
    "P0": [],
    "P1": [],
    "P2": []
  }
}
```

### Rule 6: Save Reproducible Evidence
For every finding:
1. Save the curl command to `curl-commands.sh`
2. Save raw response to appropriate evidence folder
3. Redact sensitive data (passwords, tokens) in displayed output

## Evidence Directory Structure

```
.sb-pentest-evidence/
├── README.md                    # Evidence index
├── curl-commands.sh             # All curl commands (reproducible)
├── timeline.md                  # Chronological findings
├── 01-detection/
├── 02-extraction/
├── 03-api-audit/
├── 04-storage-audit/
├── 05-auth-audit/
├── 06-realtime-audit/
├── 07-functions-audit/
└── screenshots/
```

## Quick Start Commands

```bash
# Full guided audit (recommended)
/supabase-pentest

# Generate report from findings
/supabase-report

# Compare with previous audit
/supabase-report-compare
```

## Authorization Reminder

Before running ANY audit:
- [ ] I own this application OR have explicit written authorization
- [ ] I understand all tests are logged
- [ ] I will not use findings for unauthorized purposes

---

**Remember**: Professional audits require professional documentation. Log everything.
