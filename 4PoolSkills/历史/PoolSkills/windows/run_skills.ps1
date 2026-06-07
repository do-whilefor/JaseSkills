param(
  [Parameter(Mandatory=$true)][string]$TargetRoot,
  [string]$TargetUrl = "",
  [string]$Matrix = "dynamic/role_tenant_matrix.example.windows.yaml",
  [string]$ScopeFile = ""
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$TargetRoot = (Resolve-Path -LiteralPath $TargetRoot).Path
$ScopeArgs = @()
if ($ScopeFile -ne "") {
  if (-not [System.IO.Path]::IsPathRooted($ScopeFile)) {
    $ScopeFile = Join-Path $TargetRoot $ScopeFile
  }
  if (-not (Test-Path -LiteralPath $ScopeFile)) {
    throw "Scope file not found: $ScopeFile"
  }
  $ScopeFile = (Resolve-Path -LiteralPath $ScopeFile).Path
  $ScopeArgs = @("--scope-file", $ScopeFile)
} else {
  $TargetScope = Join-Path $TargetRoot "scope.yaml"
  if (Test-Path -LiteralPath $TargetScope) {
    $ScopeFile = (Resolve-Path -LiteralPath $TargetScope).Path
    $ScopeArgs = @("--scope-file", $ScopeFile)
  } else {
    Write-Host "Using generated target-local default scope; no files are written to target root."
  }
}

& python scripts/windows_preflight.py
& python collectors/route_collector.py "$TargetRoot" @ScopeArgs --out outputs/current/win_routes.json
& python collectors/js_asset_collector.py "$TargetRoot" @ScopeArgs --out outputs/current/win_js.json
& python collectors/hidden_parameter_collector.py "$TargetRoot" @ScopeArgs --out outputs/current/win_params.json
& python analyzers/semantic_graph_builder.py "$TargetRoot" --routes outputs/current/win_routes.json --params outputs/current/win_params.json @ScopeArgs --out outputs/current/win_graph.json
& python analyzers/taint_engine.py --graph outputs/current/win_graph.json --out outputs/current/win_taint.json
& python detectors/detector_runner.py "$TargetRoot" --graph outputs/current/win_graph.json @ScopeArgs --out outputs/current/win_findings.json
& python dynamic/candidate_to_replay_plan.py --candidates outputs/current/win_findings.json --out outputs/current/win_replay_plan.json
& python evidence/evidence_manifest_builder.py --root "$TargetRoot" --candidates outputs/current/win_findings.json @ScopeArgs --out outputs/current/win_evidence_manifest.json
if ($TargetUrl -ne "") {
  & python dynamic/playwright_runner.py --plan outputs/current/win_replay_plan.json --root "$TargetRoot" @ScopeArgs --target-url "$TargetUrl" --matrix "$Matrix" --out outputs/current/win_replay_result.json
  & python dynamic/evidence_collector.py --manifest outputs/current/win_evidence_manifest.json --replay outputs/current/win_replay_result.json --root "$TargetRoot" --out outputs/current/win_evidence_manifest_stitched.json
  & python quality/quality_gate.py --candidates outputs/current/win_findings.json --evidence outputs/current/win_evidence_manifest_stitched.json --replay outputs/current/win_replay_result.json @ScopeArgs --out outputs/current/win_quality_result.json
  & python report/report_generator.py --candidates outputs/current/win_findings.json --evidence outputs/current/win_evidence_manifest_stitched.json --quality outputs/current/win_quality_result.json --out outputs/current/win_security_report.md
} else {
  & python dynamic/playwright_runner.py --plan outputs/current/win_replay_plan.json --root "$TargetRoot" @ScopeArgs --out outputs/current/win_replay_result.json
  & python quality/quality_gate.py --candidates outputs/current/win_findings.json --evidence outputs/current/win_evidence_manifest.json --replay outputs/current/win_replay_result.json @ScopeArgs --out outputs/current/win_quality_result.json
  & python report/report_generator.py --candidates outputs/current/win_findings.json --evidence outputs/current/win_evidence_manifest.json --quality outputs/current/win_quality_result.json --out outputs/current/win_security_report.md
}
Write-Host "Done. Report: outputs/current/win_security_report.md"
