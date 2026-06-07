param(
  [Parameter(Mandatory=$true)][string]$EvidenceRoot,
  [string]$Out = 'reports/js-top-tier'
)
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -ge 7) { $PSNativeCommandUseErrorActionPreference = $true }
Set-Location -Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
function Invoke-JsEndNative {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  & $Args[0] @($Args | Select-Object -Skip 1)
  if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE: $($Args -join ' ')" }
}
Invoke-JsEndNative node scripts/js_cross_platform_runner.mjs runtime:authorized-gate --evidence-root $EvidenceRoot --out $Out
Invoke-JsEndNative node scripts/js_cross_platform_runner.mjs runtime:import --evidence-root $EvidenceRoot --out $Out
Invoke-JsEndNative node scripts/js_cross_platform_runner.mjs quality --report-dir $Out
