# Native Windows Setup — No Docker
# Ollama + Open WebUI running directly on Windows
# RTX 3050 / 32GB optimized — GPU used automatically

Write-Host "==> Native AI Stack Setup (Windows)" -ForegroundColor Cyan

# ── 1. Install Ollama ──────────────────────────────────────────────────────────
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "==> Installing Ollama..." -ForegroundColor Yellow
    winget install Ollama.Ollama --silent --accept-package-agreements --accept-source-agreements
    Write-Host "Ollama installed." -ForegroundColor Green
} else {
    Write-Host "==> Ollama already installed ($(ollama --version))" -ForegroundColor Green
}

# ── 2. Set Ollama env vars for RTX 3050 / 32GB ────────────────────────────────
Write-Host "==> Configuring Ollama for RTX 3050..." -ForegroundColor Yellow
[System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL", "4", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_MAX_LOADED_MODELS", "2", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE", "10m", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_HOST", "127.0.0.1:11434", "User")
$env:OLLAMA_NUM_PARALLEL = "4"
$env:OLLAMA_MAX_LOADED_MODELS = "2"
$env:OLLAMA_KEEP_ALIVE = "10m"
$env:OLLAMA_HOST = "127.0.0.1:11434"

# ── 3. Start Ollama service ────────────────────────────────────────────────────
Write-Host "==> Starting Ollama..." -ForegroundColor Yellow
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 3

# ── 4. Pull model (fits RTX 3050 VRAM) ────────────────────────────────────────
Write-Host "==> Pulling llama3.2:3b (fits RTX 3050 VRAM)..." -ForegroundColor Yellow
ollama pull llama3.2:3b

# ── 5. Install Python if missing ──────────────────────────────────────────────
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "==> Installing Python 3.11..." -ForegroundColor Yellow
    winget install Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
    $env:PATH += ";$env:LOCALAPPDATA\Programs\Python\Python311;$env:LOCALAPPDATA\Programs\Python\Python311\Scripts"
}

# ── 6. Install Open WebUI ──────────────────────────────────────────────────────────
Write-Host "==> Installing Open WebUI..." -ForegroundColor Yellow
pip install open-webui --quiet

# ── 7. Start Open WebUI ───────────────────────────────────────────────────────
Write-Host "==> Starting Open WebUI on port 3000..." -ForegroundColor Yellow
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
$env:WEBUI_AUTH = "false"
$env:WEBUI_NAME = "Local AI Chat"
Start-Process -FilePath "open-webui" -ArgumentList "serve --port 3000" -WindowStyle Hidden
Start-Sleep -Seconds 5

# ── 8. Get IPs ────────────────────────────────────────────────────────────────
$LocalIP = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.InterfaceAlias -notmatch "Loopback" -and $_.IPAddress -notmatch "^169" } |
    Select-Object -First 1).IPAddress

$TailscaleIP = ""
if (Get-Command tailscale -ErrorAction SilentlyContinue) {
    $TailscaleIP = (tailscale ip -4 2>$null)
}

# ── 9. Summary ────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ✅  Stack is up — native Windows, no Docker            ║" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  💬  AI Chat                                            ║" -ForegroundColor Cyan
Write-Host "║      PC      : http://localhost:3000                    ║" -ForegroundColor Cyan
Write-Host "║      iPhone WiFi : http://${LocalIP}:3000" -ForegroundColor Cyan
if ($TailscaleIP) {
Write-Host "║      iPhone Cell : http://${TailscaleIP}:3000 (Tailscale)" -ForegroundColor Green
} else {
Write-Host "║      Cellular: install Tailscale → https://tailscale.com║" -ForegroundColor Yellow
}
Write-Host "╠══════════════════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  📱  Remote Desktop from iPhone:                        ║" -ForegroundColor Cyan
Write-Host "║      Install TightVNC free → https://tightvnc.com       ║" -ForegroundColor Cyan
Write-Host "║      Then use Tailscale IP to connect from anywhere     ║" -ForegroundColor Cyan
Write-Host "║  🤖  Ollama API : http://localhost:11434                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop everything: run .\stop.ps1" -ForegroundColor Gray
