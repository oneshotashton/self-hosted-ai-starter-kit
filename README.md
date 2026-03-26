# Self-hosted AI Stack — Native Windows

A fast, local AI chat and remote access setup for Windows.
**No Docker. No API keys. No cloud.** Runs directly on your hardware.

## What's included

| Tool | Purpose |
|---|---|
| [**Ollama**](https://ollama.com/) | LLM engine — native `.exe`, uses RTX 3050 GPU directly |
| [**Open WebUI**](https://github.com/open-webui/open-webui) | AI chat UI — ChatGPT-like interface in your browser |
| [**TightVNC**](https://tightvnc.com) | Remote desktop server — view your PC from iPhone |
| [**Tailscale**](https://tailscale.com) | Secure tunnel — access everything over WiFi **and cellular** |

## Quick start

```powershell
.\start.ps1
```

That's it. The script will:

1. Install Ollama via `winget` if missing
2. Configure GPU settings for RTX 3050 / 32 GB RAM
3. Pull `llama3.2:3b` (fits in 3050 VRAM)
4. Install and start Open WebUI on port 3000

## Access from iPhone

| Service | WiFi | Cellular |
|---|---|---|
| 💬 AI Chat | `http://<local-ip>:3000` | `http://<tailscale-ip>:3000` |
| 🖥️ Remote Desktop | `http://<local-ip>:6080/vnc.html` | `http://<tailscale-ip>:6080/vnc.html` |

Your IPs are printed automatically when `start.ps1` runs.

## One-time installs (free)

- **Tailscale** → [tailscale.com/download](https://tailscale.com/download) — install on PC + iPhone (same account)
- **TightVNC Server** → [tightvnc.com](https://tightvnc.com) — for remote desktop only

## Stop

```powershell
.\stop.ps1
```

## Requirements

- Windows 10/11
- NVIDIA RTX 3050 (or any GPU Ollama supports)
- 32 GB RAM recommended
- [winget](https://aka.ms/winget) (built into Windows 11)
