$ErrorActionPreference = 'Stop'
$workspace = Join-Path $env:USERPROFILE '.openclaw\workspace'
$repo = Join-Path $workspace '12pm_office_work'
$promptPath = Join-Path $workspace 'AMALA_CYBER_GUARDIAN_PROMPT.md'
$reportDir = Join-Path $workspace 'reports\cyber-guardian'
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$stamp = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$today = Get-Date -Format 'yyyy-MM-dd'
$log = Join-Path $reportDir "scheduler-$stamp.log"
try {
  "START $stamp" | Set-Content -LiteralPath $log -Encoding UTF8
  $basePrompt = Get-Content -LiteralPath $promptPath -Raw -Encoding UTF8
  $runPrompt = $basePrompt + "`r`n`r`nAUTOMATED RUN: Date $today. Return a concise Markdown daily report with date/duration, official policy URLs checked, passive checks, confirmed vs unverified findings, tools/models used, limitations, and next steps. Public authorization-first research only. Do not exploit, scan aggressively, or log in. Submit only a confirmed, high-confidence, original, explicitly in-scope finding through the verified official reporting channel. Up to three relevant proposals may be sent to verified public professional contacts while truthfully identifying Amala as Raj's AI security research assistant and honoring opt-outs."
  $job = Start-Job -ScriptBlock {
    param($p)
    $body = @{ model='qwen3:4b'; prompt=$p; stream=$false; think=$false; options=@{ num_predict=256 } } | ConvertTo-Json -Depth 6
    $r = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/generate' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 120
    $r.response
  } -ArgumentList $runPrompt
  $answer = $null
  if (Wait-Job -Job $job -Timeout 90) { $answer = (Receive-Job -Job $job -ErrorAction SilentlyContinue | Out-String).Trim() }
  Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
  if ([string]::IsNullOrWhiteSpace($answer)) {
    $answer = "## Run status`r`n`r`n- Local Qwen3:4B did not return within the 90-second limit.`r`n- No active security testing was performed.`r`n- No vulnerability is claimed.`r`n- This run is recorded for follow-up; retry the model on the next scheduled run."
    "MODEL_TIMEOUT_OR_UNAVAILABLE" | Add-Content -LiteralPath $log
  } else { "MODEL_OK" | Add-Content -LiteralPath $log }
  $reportPath = Join-Path $reportDir "$today.md"
  Set-Content -LiteralPath $reportPath -Value ("# Amala Cyber Guardian - $today`r`n`r`n$answer`r`n") -Encoding UTF8
  $repoReportDir = Join-Path $repo 'reports\cyber-guardian'
  New-Item -ItemType Directory -Force -Path $repoReportDir | Out-Null
  Copy-Item -LiteralPath $reportPath -Destination (Join-Path $repoReportDir "$today.md") -Force
  if (Test-Path (Join-Path $repo '.git')) {
    Push-Location $repo
    git add .
    $changes = git status --porcelain
    if ($changes) {
      git commit -m "Daily Amala Cyber Guardian report $today" | Out-File -FilePath $log -Append -Encoding UTF8
      git push origin main | Out-File -FilePath $log -Append -Encoding UTF8
    } else { 'No GitHub changes to push' | Out-File -FilePath $log -Append -Encoding UTF8 }
    Pop-Location
  }
  "END $(Get-Date -Format o) SUCCESS" | Add-Content -LiteralPath $log
} catch {
  "ERROR $(Get-Date -Format o) $($_.Exception.Message)" | Add-Content -LiteralPath $log
  exit 1
}
