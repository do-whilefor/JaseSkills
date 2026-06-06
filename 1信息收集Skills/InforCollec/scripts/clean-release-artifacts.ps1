param([string]$Root = ".")
$script = Join-Path $PSScriptRoot "clean_release_artifacts.py"
py -3 $script $Root
exit $LASTEXITCODE
