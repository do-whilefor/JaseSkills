param(
  [string]$ClaudeSkillsDir = "$env:USERPROFILE\.claude\skills",
  [string]$SkillName = "authorized-security-audit-system",
  [switch]$DryRun,
  [switch]$RunSelfTest
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $ClaudeSkillsDir $SkillName

if (!(Test-Path (Join-Path $Root "SKILL.md"))) { throw "Root SKILL.md not found: $Root" }
if (!(Test-Path (Join-Path $Root "_shared"))) { throw "_shared directory not found: $Root" }
if (!(Test-Path (Join-Path $Root "skills"))) { throw "skills directory not found: $Root" }
if (!(Test-Path $ClaudeSkillsDir)) { New-Item -ItemType Directory -Force -Path $ClaudeSkillsDir | Out-Null }

if ($DryRun) {
  Write-Host "DRY-RUN single-skill install $Root -> $Target"
  Write-Host "This preserves SKILL.md, _shared, skills, templates, tests, dashboard, quality gate, and scripts together."
  exit 0
}

if (Test-Path $Target) {
  $backup = "$Target.backup_$(Get-Date -Format yyyyMMdd_HHmmss)"
  Move-Item $Target $backup
  Write-Host "Backed up existing $Target -> $backup"
}

Copy-Item $Root $Target -Recurse -Force
Write-Host "Installed single skill directory: $Target"

if ($RunSelfTest) {
  Push-Location $Target
  try {
    python _shared/selftest/verify_system_integrity.py
  } finally {
    Pop-Location
  }
}
