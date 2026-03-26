# stop.ps1 — Stop Ollama, Open WebUI, and Docker AI-stack
Write-Host "==> Stopping AI stack..." -ForegroundColor Yellow

# Stop Open WebUI (pip-installed process)
Get-Process -Name "open-webui" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop any python process running open-webui (uses WMI to safely read CommandLine)
try {
    Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='python3.exe'" |
        Where-Object { $_.CommandLine -match "open.webui" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
} catch {}

# Stop Ollama
Get-Process -Name "ollama" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Stop Docker AI-stack services (if running)
$stackRoot = $PSScriptRoot
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "==> Stopping Docker services..." -ForegroundColor Yellow
    Push-Location "$stackRoot\n8n"    ; docker compose down 2>$null ; Pop-Location
    Push-Location "$stackRoot\qdrant" ; docker compose down 2>$null ; Pop-Location
    Push-Location "$stackRoot\ollama" ; docker compose --profile gpu-nvidia down 2>$null
                                        docker compose --profile cpu      down 2>$null
                                        docker compose --profile gpu-amd  down 2>$null ; Pop-Location
    Push-Location "$stackRoot\postgres"; docker compose down 2>$null ; Pop-Location
    Push-Location "$stackRoot"         ; docker compose down 2>$null ; Pop-Location
}

Write-Host "✅ Stopped." -ForegroundColor Green
