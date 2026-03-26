# launch-docker.ps1 — Full Docker AI-stack startup (bypasses UAC/permission prompts)
# Services: PostgreSQL → Ollama (gpu-nvidia) → Qdrant → n8n
# RTX 3050 / 32GB optimized

param(
    [ValidateSet("gpu-nvidia","cpu","gpu-amd")]
    [string]$Profile = "gpu-nvidia"
)

Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$stackRoot = $PSScriptRoot

Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Docker AI Stack — launching ($Profile)        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan

# ── 0. Verify Docker is running ───────────────────────────────────────────────
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker not found. Install Docker Desktop first." -ForegroundColor Red
    exit 1
}
$dockerRunning = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker Desktop is not running. Starting it..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
    Write-Host "Waiting 20s for Docker to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 20
}

# ── 1. Create shared network ──────────────────────────────────────────────────
Write-Host "==> Creating ai-stack network..." -ForegroundColor Yellow
Push-Location $stackRoot
docker compose up -d 2>&1 | Out-Null
Pop-Location

# ── 2. PostgreSQL ─────────────────────────────────────────────────────────────
Write-Host "==> Starting PostgreSQL..." -ForegroundColor Yellow
Push-Location "$stackRoot\postgres"
docker compose up -d
Pop-Location

# Wait for postgres healthy
Write-Host "==> Waiting for PostgreSQL to be healthy..." -ForegroundColor Yellow
$tries = 0
do {
    Start-Sleep -Seconds 3
    $health = docker inspect --format="{{.State.Health.Status}}" postgres 2>$null
    $tries++
} while ($health -ne "healthy" -and $tries -lt 20)
if ($health -ne "healthy") {
    Write-Host "WARNING: PostgreSQL health check timed out, continuing anyway..." -ForegroundColor Yellow
}

# ── 3. Ollama ─────────────────────────────────────────────────────────────────
Write-Host "==> Starting Ollama ($Profile)..." -ForegroundColor Yellow
Push-Location "$stackRoot\ollama"
docker compose --profile $Profile up -d
Pop-Location

# ── 4. Qdrant ─────────────────────────────────────────────────────────────────
Write-Host "==> Starting Qdrant..." -ForegroundColor Yellow
Push-Location "$stackRoot\qdrant"
docker compose up -d
Pop-Location

# ── 5. n8n ────────────────────────────────────────────────────────────────────
Write-Host "==> Starting n8n..." -ForegroundColor Yellow
Push-Location "$stackRoot\n8n"
docker compose up -d
Pop-Location

# ── 6. Get local IP ───────────────────────────────────────────────────────────
$LocalIP = (Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object { $_.InterfaceAlias -notmatch "Loopback" -and $_.IPAddress -notmatch "^169" } |
    Select-Object -First 1).IPAddress

$TailscaleIP = ""
if (Get-Command tailscale -ErrorAction SilentlyContinue) {
    $TailscaleIP = (tailscale ip -4 2>$null)
}

# ── 7. Summary ────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  ✅  Docker AI Stack is UP                              ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  🔧  n8n Automation                                     ║" -ForegroundColor Green
Write-Host "║      PC      : http://localhost:5678                    ║" -ForegroundColor Green
Write-Host "║      Network : http://${LocalIP}:5678" -ForegroundColor Green
Write-Host "║  🤖  Ollama API  : http://localhost:11434               ║" -ForegroundColor Green
Write-Host "║  📦  Qdrant DB   : http://localhost:6333                ║" -ForegroundColor Green
if ($TailscaleIP) {
Write-Host "║  📱  iPhone (Tailscale): http://${TailscaleIP}:5678" -ForegroundColor Green
}
Write-Host "╠══════════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  To stop: .\stop.ps1                                    ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
