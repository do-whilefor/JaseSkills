param(
  [string]$Root = ".",
  [string]$OutDir = "selftest/out"
)
$timeout = if ($env:SELFTEST_STEP_TIMEOUT) { $env:SELFTEST_STEP_TIMEOUT } else { "45" }
$script = Join-Path $Root "scripts/selftest-step-runner.py"
py -3 $script --root $Root --outdir $OutDir --timeout $timeout
exit $LASTEXITCODE
