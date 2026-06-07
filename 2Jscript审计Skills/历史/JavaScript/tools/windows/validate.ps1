$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -ge 7) { $PSNativeCommandUseErrorActionPreference = $true }
Set-Location -Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
& node scripts/js_cross_platform_runner.mjs windows:validate
if ($LASTEXITCODE -ne 0) { throw "Windows validation failed with exit code $LASTEXITCODE" }
