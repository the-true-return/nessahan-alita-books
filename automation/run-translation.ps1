# Unattended translation runner, started by Windows Task Scheduler every hour.
#
# Each run starts a headless Claude Code session that translates ~12,000 source
# words and stops; progress lives in the files, so the next run resumes. When the
# usage limit is reached, the session fails fast and the next hourly run retries.
# When the book is finished (automation/state/<slug>.done), the scheduled task
# removes itself.
#
# Manual run:  powershell -ExecutionPolicy Bypass -File automation\run-translation.ps1

param(
    [string]$Slug = "como-lidar-com-mulheres-2008",
    [string]$TaskName = "NessahanAlita-Translation"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$StateDir = Join-Path $Root "automation\state"
$LogDir = Join-Path $Root "automation\logs"
New-Item -ItemType Directory -Force $StateDir, $LogDir | Out-Null
$Lock = Join-Path $StateDir "$Slug.lock"
$Done = Join-Path $StateDir "$Slug.done"
$Log = Join-Path $LogDir ("{0}-{1}.log" -f $Slug, (Get-Date -Format "yyyyMMdd-HHmmss"))

function Write-Log($msg) { "$(Get-Date -Format s) $msg" | Out-File -Append -Encoding utf8 $Log }

if (Test-Path $Done) {
    Write-Log "Book already finished; removing scheduled task."
    try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop } catch {}
    exit 0
}

# One run at a time. A lock not refreshed for 2 hours is considered stale (crash).
if (Test-Path $Lock) {
    $age = (Get-Date) - (Get-Item $Lock).LastWriteTime
    if ($age.TotalHours -lt 2) { Write-Log "Another run is in progress (lock age $([int]$age.TotalMinutes) min); exiting."; exit 0 }
    Write-Log "Removing stale lock ($([int]$age.TotalHours) h)."
}
Set-Content -Path $Lock -Value $PID

try {
    $cfg = Get-Content (Join-Path $Root "config\books\$Slug.json") -Raw -Encoding utf8 | ConvertFrom-Json
    $prompt = (Get-Content (Join-Path $Root "automation\translate-book.md") -Raw -Encoding utf8).
        Replace("{{SLUG}}", $Slug).Replace("{{TITLE_PT}}", $cfg.title_pt).Replace("{{TITLE_EN}}", $cfg.title_en)

    $allowed = @(
        "Read", "Write", "Edit", "Glob", "Grep",
        "Bash(pymupdf-venv/Scripts/python.exe:*)",
        "Bash(cat:*)", "Bash(ls:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(grep:*)", "Bash(wc:*)", "Bash(sed -n:*)"
    )
    # Chain runs back to back while they make progress. Stop when the book is
    # done, when a run fails (usually the usage limit) or makes no progress;
    # the next hourly trigger then tries again.
    $py = Join-Path $Root "pymupdf-venv\Scripts\python.exe"
    function Get-Translated {
        & $py tools\status.py $Slug *> $null
        $p = Get-Content (Join-Path $Root "translations\$Slug\progress.json") -Raw -Encoding utf8 | ConvertFrom-Json
        ($p.chapters | Measure-Object -Property translated -Sum).Sum
    }
    for ($run = 1; $run -le 30; $run++) {
        Set-Content -Path $Lock -Value $PID   # refresh the lock's timestamp
        $before = Get-Translated
        Write-Log "Starting run $run for $Slug ($before segments translated)"
        # Native stderr must not abort the script (PowerShell 5.1 turns it into errors).
        $ErrorActionPreference = "Continue"
        $prompt | & claude -p --permission-mode acceptEdits --allowedTools $allowed 2>&1 |
            ForEach-Object { "$_" } | Out-File -Append -Encoding utf8 $Log
        $code = $LASTEXITCODE
        $ErrorActionPreference = "Stop"
        $after = Get-Translated
        Write-Log "Run $run finished with exit code $code ($after segments translated)"
        if (Test-Path $Done) { break }
        if ($code -ne 0) { Write-Log "Run failed (usage limit?); waiting for the next scheduled trigger."; break }
        if ($after -le $before) { Write-Log "No progress in this run; waiting for the next scheduled trigger."; break }
    }
}
catch {
    Write-Log "Runner error: $_"
}
finally {
    Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}

if (Test-Path $Done) {
    Write-Log "Book finished; removing scheduled task."
    try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop } catch {}
}
