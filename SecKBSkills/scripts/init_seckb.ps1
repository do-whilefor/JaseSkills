param(
  [string]$Root = "D:\Users\21452\AppData\SecKB"
)

$dirs = @(
  "indexes",
  "sources\official-advisories",
  "sources\cve-nvd-kev",
  "sources\github-security-advisories",
  "sources\vendor-advisories",
  "sources\src-platform-rules",
  "sources\bug-bounty-reports",
  "sources\tool-docs-releases",
  "sources\research-blogs",
  "vulns\web",
  "vulns\authz-idor",
  "vulns\auth-session-token",
  "vulns\ssrf",
  "vulns\rce",
  "vulns\injection",
  "vulns\file-upload-file-read",
  "vulns\deserialization",
  "vulns\xss-csrf",
  "vulns\business-logic",
  "vulns\cloud-ci-cd-supply-chain",
  "vulns\frontend-js",
  "code-audit\javascript-typescript",
  "code-audit\python",
  "code-audit\java",
  "code-audit\php",
  "code-audit\go",
  "code-audit\ruby",
  "code-audit\rust",
  "code-audit\dotnet",
  "code-audit\mobile-extension-electron",
  "templates\vuln-templates",
  "templates\report-templates",
  "templates\dynamic-validation-templates",
  "templates\false-positive-checklists",
  "templates\cannot-report-reasons",
  "src-rules\domestic",
  "src-rules\international",
  "src-rules\normalized",
  "toolchain\releases",
  "toolchain\readme-digests",
  "toolchain\command-templates",
  "toolchain\integration-notes",
  "labs\reproducible-cves",
  "labs\patch-diff",
  "labs\local-targets",
  "labs\notes",
  "evidence\manifests",
  "evidence\request-response",
  "evidence\screenshots",
  "evidence\code-snippets",
  "evidence\reproduction-logs",
  "review\needs-human-confirmation",
  "review\conflicts",
  "review\stale-items",
  "review\rejected",
  "review\promoted",
  "scripts"
)

New-Item -ItemType Directory -Force -Path $Root | Out-Null
foreach ($d in $dirs) {
  New-Item -ItemType Directory -Force -Path (Join-Path $Root $d) | Out-Null
}

$claude = @"
# SecKB Entry

默认先读取 indexes/master-index.json，再根据任务读取具体索引和细节。

安全边界：只允许学习公开资料；动态验证只允许本机、靶场、本地开源项目或明确授权环境；不允许未授权第三方目标、DoS、批量扫描、数据破坏、真实敏感数据读取、权限维持、横向移动或 MITM。

质量门槛：不确定内容进入 needs_review，冲突进入 conflict，过期进入 stale，低可信进入 rejected。只有来源、日期、版本、影响、边界、误报条件、不可报告原因、修复建议、授权验证方法、tags 和索引入口齐全的记录才能 promoted。
"@

Set-Content -Path (Join-Path $Root "CLAUDE.md") -Value $claude -Encoding UTF8
Set-Content -Path (Join-Path $Root "README.md") -Value "# SecKB`n`nInitialized local SecKB." -Encoding UTF8
Write-Host "Initialized SecKB at $Root"
