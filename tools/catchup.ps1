# Catch-up trigger for the daily episode.
# GitHub's scheduler sometimes drops runs (2026-11-18: every 5:15-7:15 AM attempt, first run 12:51 PM).
# This runs from the operator's morning run (AIOS-MorningRun, StartWhenAvailable) and from anywhere else:
# if today's episode is not on main and no run is active, start the workflow. Safe to run twice: the
# workflow exits at once when the episode exists, and runs queue one at a time.
# Exit 0 = episode exists or a run is now active/started. Exit 1 = could not check or start (loud).
param([switch]$DryRun, [string]$AssumeDate = '')
$ErrorActionPreference = 'Stop'
$Repo = 'AutomAIton/amf-1cfbea55'
function Log($m) { Write-Output ("{0} catchup: {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $m) }
Log "START dryrun=$($DryRun.IsPresent)"
try {
    $central = [TimeZoneInfo]::FindSystemTimeZoneById('Central Standard Time')
    $today = [TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [TimeZoneInfo]::Utc, $central).ToString('yyyy-MM-dd')
    if ($AssumeDate) { $today = $AssumeDate }  # test hook: pretend today is another day
    $raw = (& gh api "repos/$Repo/contents/data/history.json" -H 'Accept: application/vnd.github.raw' 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) { throw "gh api failed: $raw" }
    $history = $raw | ConvertFrom-Json
    $have = @($history.episodes | Where-Object { $_.date -eq $today }).Count -gt 0
    if ($have) { Log "episode $today already published"; exit 0 }

    $runs = (& gh run list --repo $Repo --workflow daily.yml --limit 10 --json status 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) { throw "gh run list failed: $runs" }
    $active = @($runs | ConvertFrom-Json | Where-Object { $_.status -in 'queued', 'in_progress', 'pending', 'waiting' }).Count
    if ($active -gt 0) { Log "episode $today missing but $active run(s) active; leaving them to finish"; exit 0 }

    if ($DryRun) { Log "DRYRUN would start workflow for $today"; exit 0 }
    $out = (& gh workflow run daily.yml --repo $Repo --ref main 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) { throw "gh workflow run failed: $out" }
    Log "episode $today missing, no active run: workflow started"
    exit 0
} catch {
    Log "FAILED: $($_.Exception.Message)"
    exit 1
}
