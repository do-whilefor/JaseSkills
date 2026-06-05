param(
  [string]$Root = "D:\Users\21452\AppData\SecKB",
  [string]$PlanOut = "collection-plan.json"
)

$plan = [ordered]@{
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  note = "This script is a safe collection planner. Configure official source URLs before live collection. Do not claim live updates unless actual collection is implemented and logged."
  target_sources = @(
    "MITRE CVE",
    "NVD",
    "CISA KEV",
    "GitHub Security Advisories",
    "Vendor official advisories",
    "SRC official rules",
    "Tool official releases and README"
  )
  default_review_status = "needs_review"
}

$path = Join-Path $Root $PlanOut
$plan | ConvertTo-Json -Depth 5 | Set-Content -Path $path -Encoding UTF8
Write-Host "Wrote safe collection plan to $path"
