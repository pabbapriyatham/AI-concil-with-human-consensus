param([switch]$Live)
$ErrorActionPreference = "Stop"
$project = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $project
$python = Join-Path $project ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) { throw "Create .venv and install dependencies first. See docs/development/SETUP.md." }
if ($Live) { $env:DEV_MODE = "false" }
$backend = Start-Process -FilePath $python -ArgumentList "-m", "backend.main" -WorkingDirectory $project -WindowStyle Hidden -PassThru
$frontend = Start-Process -FilePath "npm.cmd" -ArgumentList "run", "dev", "--", "--host", "127.0.0.1" -WorkingDirectory (Join-Path $project "frontend") -WindowStyle Hidden -PassThru
Write-Host "Mahthildis: http://localhost:5173 (backend :8001). Press Ctrl+C to stop."
try { while (-not $backend.HasExited -and -not $frontend.HasExited) { Start-Sleep -Seconds 1 } }
finally {
    foreach ($process in @($backend, $frontend)) {
        if (-not $process.HasExited) { & taskkill /PID $process.Id /T /F | Out-Null }
    }
}
