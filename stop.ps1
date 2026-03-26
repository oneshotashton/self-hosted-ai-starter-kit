# stop.ps1 — Stop Ollama and Open WebUI native processes
Write-Host "==> Stopping AI stack..." -ForegroundColor Yellow

# Stop Open WebUI
Get-Process -Name "open-webui" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "python" -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowTitle -match "open.webui" -or $_.CommandLine -match "open.webui" } |
    Stop-Process -Force -ErrorAction SilentlyContinue

# Stop Ollama
Get-Process -Name "ollama" -ErrorAction SilentlyContinue | Stop-Process -Force

Write-Host "✅ Stopped." -ForegroundColor Green
