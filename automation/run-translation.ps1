# Unattended translation runner, started by Windows Task Scheduler every hour.
#
# Works through automation/queue.txt one book at a time. For the current book it
# chains headless Claude Code sessions (each translates ~12,000 source words and
# stops) while they make progress. When a session fails (usually the usage
# limit) or makes no progress, it waits for the next hourly trigger. When a
# book is finished (automation/state/<slug>.done), the runner commits and
# pushes it and starts the next book. When the queue is empty, the scheduled
# task removes itself.
#
# Manual run:  powershell -ExecutionPolicy Bypass -File automation\run-translation.ps1

param([string]$TaskName = "NessahanAlita-Translation")

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$StateDir = Join-Path $Root "automation\state"
$LogDir = Join-Path $Root "automation\logs"
New-Item -ItemType Directory -Force $StateDir, $LogDir | Out-Null
$Lock = Join-Path $StateDir "runner.lock"
$Log = Join-Path $LogDir ("run-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
$Py = Join-Path $Root "pymupdf-venv\Scripts\python.exe"

function Write-Log($msg) { "$(Get-Date -Format s) $msg" | Out-File -Append -Encoding utf8 $Log }

function Invoke-Native([scriptblock]$cmd) {
    # Native stderr must not abort the script (PowerShell 5.1 turns it into errors).
    $ErrorActionPreference = "Continue"
    & $cmd 2>&1 | ForEach-Object { "$_" } | Out-File -Append -Encoding utf8 $Log
    $code = $LASTEXITCODE
    $ErrorActionPreference = "Stop"
    return $code
}

function Get-NextBook {
    Get-Content (Join-Path $Root "automation\queue.txt") -Encoding utf8 |
        Where-Object { $_ -and -not $_.StartsWith("#") } |
        ForEach-Object { $_.Trim() } |
        Where-Object { -not (Test-Path (Join-Path $StateDir "$_.done")) } |
        Select-Object -First 1
}

function Get-Translated($slug) {
    & $Py tools\status.py $slug *> $null
    $p = Get-Content (Join-Path $Root "translations\$slug\progress.json") -Raw -Encoding utf8 | ConvertFrom-Json
    ($p.chapters | Measure-Object -Property translated -Sum).Sum
}

function Publish-Book($slug, $cfg) {
    # Commit everything for the finished book and push. A failed push is
    # retried at the start of every later run.
    Invoke-Native { git add -A } | Out-Null
    $msg = "Translate $($cfg.title_pt) into English ($($cfg.title_en))"
    $body = "Unattended translation run: translations, QA reports, glossary updates and the final PDF in books/.`n`nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
    $code = Invoke-Native { git commit -m $msg -m $body }
    Write-Log "git commit for $slug exited with $code"
    Push-Pending
}

function Push-Pending {
    $ahead = (git rev-list --count "@{u}..HEAD" 2>$null)
    if ($ahead -and [int]$ahead -gt 0) {
        $code = Invoke-Native { git push origin HEAD }
        Write-Log "git push ($ahead commit(s)) exited with $code"
    }
}

# One runner at a time. The lock is refreshed before every session; one not
# refreshed for 2 hours is considered stale (crash).
if (Test-Path $Lock) {
    $age = (Get-Date) - (Get-Item $Lock).LastWriteTime
    if ($age.TotalHours -lt 2) { Write-Log "Another run is in progress (lock age $([int]$age.TotalMinutes) min); exiting."; exit 0 }
    Write-Log "Removing stale lock ($([int]$age.TotalHours) h)."
}
Set-Content -Path $Lock -Value $PID

try {
    Push-Pending
    $allowed = @(
        "Read", "Write", "Edit", "Glob", "Grep",
        "Bash(pymupdf-venv/Scripts/python.exe:*)",
        "Bash(cat:*)", "Bash(ls:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(grep:*)", "Bash(wc:*)", "Bash(sed -n:*)"
    )
    for ($session = 1; $session -le 60; $session++) {
        $slug = Get-NextBook
        if (-not $slug) { Write-Log "Queue finished."; break }
        $cfg = Get-Content (Join-Path $Root "config\books\$slug.json") -Raw -Encoding utf8 | ConvertFrom-Json
        $prompt = (Get-Content (Join-Path $Root "automation\translate-book.md") -Raw -Encoding utf8).
            Replace("{{SLUG}}", $slug).Replace("{{TITLE_PT}}", $cfg.title_pt).Replace("{{TITLE_EN}}", $cfg.title_en)

        Set-Content -Path $Lock -Value $PID   # refresh the lock's timestamp
        $before = Get-Translated $slug
        Write-Log "Session $session for $slug starting ($before segments translated)"
        $code = Invoke-Native { $prompt | & claude -p --permission-mode acceptEdits --allowedTools $allowed }
        $after = Get-Translated $slug
        Write-Log "Session $session for $slug finished with exit code $code ($after segments translated)"

        if (Test-Path (Join-Path $StateDir "$slug.done")) {
            Write-Log "$slug finished; committing and pushing."
            Publish-Book $slug $cfg
            continue
        }
        if ($code -ne 0) { Write-Log "Session failed (usage limit?); waiting for the next scheduled trigger."; break }
        if ($after -le $before) { Write-Log "No progress; waiting for the next scheduled trigger."; break }
    }
}
catch {
    Write-Log "Runner error: $_"
}
finally {
    Remove-Item $Lock -Force -ErrorAction SilentlyContinue
}

if (-not (Get-NextBook)) {
    Write-Log "All books in the queue are finished; removing scheduled task."
    try { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop } catch {}
}
