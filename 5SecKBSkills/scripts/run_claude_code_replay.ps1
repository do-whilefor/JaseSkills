param(
  [switch]$Execute
)
$root = Split-Path -Parent $PSScriptRoot
$cases = Join-Path $root "tests\claude-code-replay\replay-cases.json"
$reports = Join-Path $root "reports"
New-Item -ItemType Directory -Force $reports | Out-Null
$out = Join-Path $reports ($(if ($Execute) {"claude-code-replay-live.json"} else {"claude-code-replay-dryrun.json"}))
if ($Execute) {
  python (Join-Path $root "scripts\claude_code_replay.py") $cases $out --execute
} else {
  python (Join-Path $root "scripts\claude_code_replay.py") $cases $out
}
