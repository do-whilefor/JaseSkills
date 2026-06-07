$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -ge 7) { $PSNativeCommandUseErrorActionPreference = $true }
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
function Invoke-JsEndNative {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  & $Args[0] @($Args | Select-Object -Skip 1)
  if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE: $($Args -join ' ')" }
}
Invoke-JsEndNative python scripts/install_and_env_check.py --root $Root --out reports/env-check
if (Get-Command npm -ErrorAction SilentlyContinue) {
  Invoke-JsEndNative npm install
  Invoke-JsEndNative npx playwright install chromium
}
Invoke-JsEndNative python scripts/install_and_env_check.py --root $Root --out reports/env-check
