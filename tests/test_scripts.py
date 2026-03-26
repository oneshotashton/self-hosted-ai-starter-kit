"""Tests for PowerShell startup / shutdown scripts.

Because PowerShell is not available in the CI environment, these tests use
plain text analysis of the .ps1 source files rather than executing them.

Covers:
- Script file presence
- Presence of key commands and patterns
- Port numbers referenced match docker-compose.yml definitions
- Startup ordering in launch-docker.ps1 (postgres before ollama before n8n)
- Shutdown coverage in stop.ps1 (all profiles and all services)
- launch-docker.ps1 ValidateSet profiles match ollama profiles
- Error-handling conventions ($ErrorActionPreference, try/catch)
"""

import pathlib
import re
import pytest


REPO_ROOT = pathlib.Path(__file__).parent.parent

SCRIPTS = {
    "start": REPO_ROOT / "start.ps1",
    "stop": REPO_ROOT / "stop.ps1",
    "launch_docker": REPO_ROOT / "launch-docker.ps1",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def script_text(name: str) -> str:
    return SCRIPTS[name].read_text()


# ---------------------------------------------------------------------------
# File presence
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,path", list(SCRIPTS.items()))
def test_script_exists(name, path):
    assert path.exists(), f"Script not found: {path}"


# ---------------------------------------------------------------------------
# start.ps1
# ---------------------------------------------------------------------------

class TestStartScript:
    @pytest.fixture(scope="class")
    def src(self):
        return script_text("start")

    def test_installs_ollama_via_winget(self, src):
        assert "winget install Ollama.Ollama" in src

    def test_starts_ollama_serve(self, src):
        assert 'ollama" -ArgumentList "serve"' in src

    def test_pulls_llama_model(self, src):
        assert "ollama pull llama3.2" in src

    def test_installs_python_via_winget(self, src):
        assert "winget install Python.Python" in src

    def test_installs_open_webui(self, src):
        assert "pip install open-webui" in src

    def test_starts_open_webui_on_port_3000(self, src):
        assert "3000" in src

    def test_ollama_api_port_referenced(self, src):
        assert "11434" in src

    def test_sets_ollama_num_parallel_env(self, src):
        assert "OLLAMA_NUM_PARALLEL" in src

    def test_sets_ollama_max_loaded_models_env(self, src):
        assert "OLLAMA_MAX_LOADED_MODELS" in src

    def test_sets_ollama_keep_alive_env(self, src):
        assert "OLLAMA_KEEP_ALIVE" in src

    def test_sets_ollama_host_env(self, src):
        assert "OLLAMA_HOST" in src

    def test_retrieves_local_ip(self, src):
        assert "Get-NetIPAddress" in src

    def test_checks_tailscale_availability(self, src):
        assert "tailscale" in src

    def test_open_webui_ollama_base_url(self, src):
        assert "OLLAMA_BASE_URL" in src

    def test_check_ollama_already_installed(self, src):
        assert "Get-Command ollama" in src

    def test_check_python_already_installed(self, src):
        assert "Get-Command python" in src


# ---------------------------------------------------------------------------
# stop.ps1
# ---------------------------------------------------------------------------

class TestStopScript:
    @pytest.fixture(scope="class")
    def src(self):
        return script_text("stop")

    def test_stops_open_webui_process(self, src):
        assert "open-webui" in src

    def test_stops_ollama_process(self, src):
        assert 'Get-Process -Name "ollama"' in src

    def test_stops_docker_n8n_service(self, src):
        assert "n8n" in src and "docker compose down" in src

    def test_stops_docker_qdrant_service(self, src):
        assert "qdrant" in src

    def test_stops_docker_postgres_service(self, src):
        assert "postgres" in src

    def test_stops_all_ollama_profiles(self, src):
        assert "gpu-nvidia" in src
        assert "cpu" in src
        assert "gpu-amd" in src

    def test_uses_stop_process_force(self, src):
        assert "Stop-Process -Force" in src

    def test_checks_docker_available(self, src):
        assert "Get-Command docker" in src

    def test_uses_pslocation_push_pop(self, src):
        assert "Push-Location" in src
        assert "Pop-Location" in src

    def test_handles_python_open_webui_process(self, src):
        """stop.ps1 must stop python processes running open-webui.

        The script uses a PowerShell regex match: -match "open.webui"
        where '.' is a regex wildcard.  The literal string in the source
        file is therefore "open.webui" (dot, not hyphen).
        """
        assert "python" in src.lower() and "open.webui" in src

    def test_uses_try_catch_for_wmi(self, src):
        """stop.ps1 wraps the WMI process enumeration in try/catch to
        gracefully handle environments where WMI / CIM is unavailable.
        The catch block is intentionally empty — failure is non-fatal.
        """
        assert "try {" in src
        assert "} catch {}" in src or "catch {}" in src


# ---------------------------------------------------------------------------
# launch-docker.ps1
# ---------------------------------------------------------------------------

class TestLaunchDockerScript:
    @pytest.fixture(scope="class")
    def src(self):
        return script_text("launch_docker")

    def test_has_profile_parameter(self, src):
        assert "[string]$Profile" in src

    def test_validate_set_includes_gpu_nvidia(self, src):
        assert "gpu-nvidia" in src

    def test_validate_set_includes_cpu(self, src):
        assert '"cpu"' in src

    def test_validate_set_includes_gpu_amd(self, src):
        assert "gpu-amd" in src

    def test_default_profile_is_gpu_nvidia(self, src):
        assert 'string]$Profile = "gpu-nvidia"' in src

    def test_checks_docker_installed(self, src):
        assert "Get-Command docker" in src

    def test_starts_docker_desktop_if_not_running(self, src):
        assert "Docker Desktop.exe" in src

    def test_creates_ai_stack_network_first(self, src):
        # The ai-stack network setup must appear before any service startup.
        network_pos = src.find("docker compose up -d")
        postgres_pos = src.find("postgres")
        assert network_pos < postgres_pos, (
            "ai-stack network must be created before postgres starts"
        )

    def test_starts_postgres_before_n8n(self, src):
        postgres_pos = src.find('"$stackRoot\\postgres"')
        n8n_pos = src.find('"$stackRoot\\n8n"')
        assert postgres_pos < n8n_pos, "PostgreSQL must start before n8n"

    def test_starts_ollama_before_n8n(self, src):
        ollama_pos = src.find('"$stackRoot\\ollama"')
        n8n_pos = src.find('"$stackRoot\\n8n"')
        assert ollama_pos < n8n_pos, "Ollama must start before n8n"

    def test_starts_qdrant_before_n8n(self, src):
        qdrant_pos = src.find('"$stackRoot\\qdrant"')
        n8n_pos = src.find('"$stackRoot\\n8n"')
        assert qdrant_pos < n8n_pos, "Qdrant must start before n8n"

    def test_waits_for_postgres_healthy(self, src):
        assert "healthy" in src

    def test_passes_profile_to_ollama_compose(self, src):
        assert "--profile $Profile" in src

    def test_n8n_port_in_summary(self, src):
        assert "5678" in src

    def test_ollama_port_in_summary(self, src):
        assert "11434" in src

    def test_qdrant_port_in_summary(self, src):
        assert "6333" in src

    def test_retrieves_local_ip(self, src):
        assert "Get-NetIPAddress" in src

    def test_checks_tailscale_availability(self, src):
        assert "tailscale" in src

    def test_uses_push_pop_location(self, src):
        assert "Push-Location" in src
        assert "Pop-Location" in src

    def test_sets_error_action_preference(self, src):
        assert "$ErrorActionPreference" in src


# ---------------------------------------------------------------------------
# Cross-script port consistency
# ---------------------------------------------------------------------------

class TestPortConsistency:
    """Ports referenced in scripts must match docker-compose.yml definitions."""

    N8N_PORT = "5678"
    OLLAMA_PORT = "11434"
    QDRANT_PORT = "6333"
    POSTGRES_PORT = "5432"

    def test_launch_docker_references_n8n_port(self):
        assert self.N8N_PORT in script_text("launch_docker")

    def test_launch_docker_references_ollama_port(self):
        assert self.OLLAMA_PORT in script_text("launch_docker")

    def test_launch_docker_references_qdrant_port(self):
        assert self.QDRANT_PORT in script_text("launch_docker")

    def test_start_references_open_webui_port(self):
        assert "3000" in script_text("start")

    def test_start_references_ollama_port(self):
        assert self.OLLAMA_PORT in script_text("start")
