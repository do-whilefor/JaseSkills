param(
  [switch]$InstallPlaywright = $true
)
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -ge 7) { $PSNativeCommandUseErrorActionPreference = $true }
Set-Location -Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
function Invoke-JsEndNative {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  & $Args[0] @($Args | Select-Object -Skip 1)
  if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE: $($Args -join ' ')" }
}
Write-Host '[JS-End] Windows install starting in' (Get-Location)
$node = Get-Command node -ErrorAction SilentlyContinue
if (-not $node) { throw 'Node.js is missing. Install Node.js 18+ and reopen PowerShell.' }
$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python -and -not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python 3 is missing. Install Python 3.10+ and add it to PATH.' }
Invoke-JsEndNative npm install
if ($InstallPlaywright) {
  Invoke-JsEndNative npx playwright install chromium
}
Invoke-JsEndNative node scripts/js_cross_platform_runner.mjs windows:check
