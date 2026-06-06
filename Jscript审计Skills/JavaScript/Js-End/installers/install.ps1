$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
python scripts/install_and_env_check.py --root $Root --out reports/env-check
if (Get-Command npm -ErrorAction SilentlyContinue) {
  npm install
  npx playwright install chromium
}
python scripts/install_and_env_check.py --root $Root --out reports/env-check
