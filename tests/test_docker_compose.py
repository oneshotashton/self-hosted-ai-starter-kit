"""Tests for all docker-compose.yml files in the repository.

Covers:
- YAML validity (handled by the conftest.py fixtures which parse on load)
- Shared ai-stack network definition and references
- Service definitions, port mappings, volume mounts
- Image tags and health checks
- Hardened n8n task-runner security settings
- Ollama hardware profiles (cpu / gpu-nvidia / gpu-amd)
"""

import pathlib
import pytest
import yaml

REPO_ROOT = pathlib.Path(__file__).parent.parent

COMPOSE_FILES = [
    REPO_ROOT / "docker-compose.yml",
    REPO_ROOT / "n8n" / "docker-compose.yml",
    REPO_ROOT / "ollama" / "docker-compose.yml",
    REPO_ROOT / "postgres" / "docker-compose.yml",
    REPO_ROOT / "qdrant" / "docker-compose.yml",
]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _services(compose: dict) -> dict:
    """Return the services dict, or {} if not present."""
    return compose.get("services") or {}


# ---------------------------------------------------------------------------
# File presence
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", COMPOSE_FILES, ids=[p.parent.name or "root" for p in COMPOSE_FILES])
def test_compose_file_exists(path):
    assert path.exists(), f"docker-compose.yml not found: {path}"


# ---------------------------------------------------------------------------
# YAML validity — proven by successful fixture load (each fixture calls
# yaml.safe_load; if a file is invalid YAML the fixture itself errors).
# We add an explicit re-parse test to get cleaner failure messages.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", COMPOSE_FILES, ids=[p.parent.name or "root" for p in COMPOSE_FILES])
def test_compose_yaml_is_valid(path):
    with path.open() as fh:
        doc = yaml.safe_load(fh)
    assert isinstance(doc, dict), f"{path} did not parse to a dict"


# ---------------------------------------------------------------------------
# Root compose — shared network
# ---------------------------------------------------------------------------

class TestRootCompose:
    def test_has_networks_key(self, root_compose):
        assert "networks" in root_compose

    def test_ai_stack_network_defined(self, root_compose):
        assert "ai-stack" in root_compose["networks"]

    def test_ai_stack_driver_is_bridge(self, root_compose):
        net = root_compose["networks"]["ai-stack"]
        assert net.get("driver") == "bridge"

    def test_ai_stack_has_explicit_name(self, root_compose):
        net = root_compose["networks"]["ai-stack"]
        assert net.get("name") == "ai-stack"

    def test_root_compose_has_no_services(self, root_compose):
        """Root compose only defines the network; services live in sub-dirs."""
        services = _services(root_compose)
        assert len(services) == 0


# ---------------------------------------------------------------------------
# Service composes — each must reference ai-stack as an external network
# ---------------------------------------------------------------------------

SERVICE_COMPOSES = ["n8n_compose", "ollama_compose", "postgres_compose", "qdrant_compose"]


@pytest.mark.parametrize("fixture_name", SERVICE_COMPOSES)
def test_service_compose_has_external_ai_stack_network(fixture_name, request):
    compose = request.getfixturevalue(fixture_name)
    networks = compose.get("networks", {})
    assert "ai-stack" in networks, f"'ai-stack' network missing in {fixture_name}"
    assert networks["ai-stack"].get("external") is True, (
        f"'ai-stack' network should be external in {fixture_name}"
    )


# ---------------------------------------------------------------------------
# n8n docker-compose
# ---------------------------------------------------------------------------

class TestN8nCompose:
    def test_has_n8n_service(self, n8n_compose):
        assert "n8n" in _services(n8n_compose)

    def test_has_n8n_import_service(self, n8n_compose):
        assert "n8n-import" in _services(n8n_compose)

    def test_has_n8n_task_runner_service(self, n8n_compose):
        assert "n8n-task-runner" in _services(n8n_compose)

    def test_n8n_port_5678(self, n8n_compose):
        ports = _services(n8n_compose)["n8n"].get("ports", [])
        assert any("5678" in str(p) for p in ports), "n8n must expose port 5678"

    def test_n8n_uses_n8n_image(self, n8n_compose):
        image = _services(n8n_compose)["n8n"].get("image", "")
        assert "n8nio/n8n" in image

    def test_n8n_restart_policy(self, n8n_compose):
        restart = _services(n8n_compose)["n8n"].get("restart")
        assert restart == "unless-stopped"

    def test_n8n_has_persistent_volume(self, n8n_compose):
        volumes = _services(n8n_compose)["n8n"].get("volumes", [])
        volume_strings = [str(v) for v in volumes]
        assert any("n8n_storage" in v for v in volume_strings), (
            "n8n service must mount n8n_storage volume"
        )

    def test_n8n_volume_defined_at_top_level(self, n8n_compose):
        assert "n8n_storage" in (n8n_compose.get("volumes") or {})

    def test_n8n_import_depends_on_postgres(self, n8n_compose):
        depends = _services(n8n_compose)["n8n-import"].get("depends_on", [])
        assert "postgres" in depends

    def test_n8n_depends_on_n8n_import(self, n8n_compose):
        depends = _services(n8n_compose)["n8n"].get("depends_on", [])
        assert "n8n-import" in depends

    def test_n8n_import_mounts_demo_data(self, n8n_compose):
        volumes = _services(n8n_compose)["n8n-import"].get("volumes", [])
        assert any("demo-data" in str(v) for v in volumes)

    # Hardened task-runner assertions
    def test_task_runner_uses_distroless_image(self, n8n_compose):
        image = _services(n8n_compose)["n8n-task-runner"].get("image", "")
        assert "distroless" in image, "task-runner should use the distroless image"

    def test_task_runner_read_only_filesystem(self, n8n_compose):
        read_only = _services(n8n_compose)["n8n-task-runner"].get("read_only")
        assert read_only is True, "task-runner filesystem must be read-only"

    def test_task_runner_runs_as_nobody_user(self, n8n_compose):
        user = _services(n8n_compose)["n8n-task-runner"].get("user")
        assert user == "65532:65532", "task-runner must run as nobody (65532:65532)"

    def test_task_runner_has_tmpfs(self, n8n_compose):
        tmpfs = _services(n8n_compose)["n8n-task-runner"].get("tmpfs", [])
        assert len(tmpfs) > 0, "task-runner needs a tmpfs scratch directory"

    def test_task_runner_tmpfs_size_limit(self, n8n_compose):
        tmpfs = _services(n8n_compose)["n8n-task-runner"].get("tmpfs", [])
        assert any("128m" in str(entry) for entry in tmpfs), (
            "task-runner tmpfs should be limited to 128m"
        )

    def test_task_runner_depends_on_n8n(self, n8n_compose):
        depends = _services(n8n_compose)["n8n-task-runner"].get("depends_on", [])
        assert "n8n" in depends

    def test_task_runner_restart_policy(self, n8n_compose):
        restart = _services(n8n_compose)["n8n-task-runner"].get("restart")
        assert restart == "unless-stopped"

    def test_n8n_env_includes_db_type(self, n8n_compose):
        """The shared env anchor should set DB_TYPE=postgresdb."""
        anchor = n8n_compose.get("x-n8n-env") or {}
        assert anchor.get("DB_TYPE") == "postgresdb"

    def test_n8n_env_includes_diagnostics_disabled(self, n8n_compose):
        anchor = n8n_compose.get("x-n8n-env") or {}
        assert anchor.get("N8N_DIAGNOSTICS_ENABLED") == "false"

    def test_n8n_env_includes_personalization_disabled(self, n8n_compose):
        anchor = n8n_compose.get("x-n8n-env") or {}
        assert anchor.get("N8N_PERSONALIZATION_ENABLED") == "false"

    def test_n8n_uses_ai_stack_network(self, n8n_compose):
        networks = _services(n8n_compose)["n8n"].get("networks", [])
        assert "ai-stack" in networks


# ---------------------------------------------------------------------------
# Ollama docker-compose
# ---------------------------------------------------------------------------

class TestOllamaCompose:
    PROFILES = ["cpu", "gpu-nvidia", "gpu-amd"]
    OLLAMA_SERVICES = ["ollama-cpu", "ollama-gpu", "ollama-gpu-amd"]
    PULL_SERVICES = ["ollama-pull-llama-cpu", "ollama-pull-llama-gpu", "ollama-pull-llama-gpu-amd"]

    def test_ollama_volume_defined(self, ollama_compose):
        assert "ollama_storage" in (ollama_compose.get("volumes") or {})

    @pytest.mark.parametrize("svc", OLLAMA_SERVICES)
    def test_ollama_service_exists(self, svc, ollama_compose):
        assert svc in _services(ollama_compose), f"Service '{svc}' not found"

    @pytest.mark.parametrize("svc,profile", zip(OLLAMA_SERVICES, PROFILES))
    def test_ollama_service_has_correct_profile(self, svc, profile, ollama_compose):
        profiles = _services(ollama_compose)[svc].get("profiles", [])
        assert profile in profiles

    @pytest.mark.parametrize("svc", PULL_SERVICES)
    def test_pull_service_exists(self, svc, ollama_compose):
        assert svc in _services(ollama_compose), f"Pull service '{svc}' not found"

    @pytest.mark.parametrize("pull_svc,profile", zip(PULL_SERVICES, PROFILES))
    def test_pull_service_has_correct_profile(self, pull_svc, profile, ollama_compose):
        profiles = _services(ollama_compose)[pull_svc].get("profiles", [])
        assert profile in profiles

    def test_ollama_cpu_uses_standard_image(self, ollama_compose):
        # cpu and gpu-nvidia use the same standard image
        image = _services(ollama_compose)["ollama-cpu"].get("image", "")
        assert "ollama/ollama" in image
        assert "rocm" not in image

    def test_ollama_gpu_amd_uses_rocm_image(self, ollama_compose):
        image = _services(ollama_compose)["ollama-gpu-amd"].get("image", "")
        assert "rocm" in image

    def test_ollama_gpu_nvidia_has_gpu_reservation(self, ollama_compose):
        svc = _services(ollama_compose)["ollama-gpu"]
        deploy = svc.get("deploy", {})
        devices = (
            deploy.get("resources", {})
                  .get("reservations", {})
                  .get("devices", [])
        )
        assert len(devices) > 0, "gpu-nvidia service must reserve a GPU"
        assert any(d.get("driver") == "nvidia" for d in devices)

    def test_ollama_gpu_amd_has_kfd_device(self, ollama_compose):
        devices = _services(ollama_compose)["ollama-gpu-amd"].get("devices", [])
        assert any("kfd" in str(d) for d in devices)

    def test_pull_llama_cpu_depends_on_ollama_cpu(self, ollama_compose):
        depends = _services(ollama_compose)["ollama-pull-llama-cpu"].get("depends_on", [])
        assert "ollama-cpu" in depends

    def test_pull_llama_gpu_depends_on_ollama_gpu(self, ollama_compose):
        depends = _services(ollama_compose)["ollama-pull-llama-gpu"].get("depends_on", [])
        assert "ollama-gpu" in depends

    def test_pull_llama_gpu_amd_depends_on_ollama_gpu_amd(self, ollama_compose):
        depends = _services(ollama_compose)["ollama-pull-llama-gpu-amd"].get("depends_on", [])
        assert "ollama-gpu-amd" in depends

    def test_init_ollama_pulls_llama3_model(self, ollama_compose):
        """The shared init anchor command must pull a llama3.2 model."""
        init = ollama_compose.get("x-init-ollama") or {}
        command = init.get("command", [])
        command_str = " ".join(str(c) for c in command)
        assert "llama3.2" in command_str


# ---------------------------------------------------------------------------
# PostgreSQL docker-compose
# ---------------------------------------------------------------------------

class TestPostgresCompose:
    def test_postgres_service_exists(self, postgres_compose):
        assert "postgres" in _services(postgres_compose)

    def test_postgres_uses_alpine_image(self, postgres_compose):
        image = _services(postgres_compose)["postgres"].get("image", "")
        assert "postgres:16-alpine" == image

    def test_postgres_port_5432(self, postgres_compose):
        ports = _services(postgres_compose)["postgres"].get("ports", [])
        assert any("5432" in str(p) for p in ports)

    def test_postgres_has_health_check(self, postgres_compose):
        hc = _services(postgres_compose)["postgres"].get("healthcheck")
        assert hc is not None, "postgres must have a healthcheck"

    def test_postgres_health_check_uses_pg_isready(self, postgres_compose):
        hc = _services(postgres_compose)["postgres"]["healthcheck"]
        test_cmd = hc.get("test", [])
        assert any("pg_isready" in str(part) for part in test_cmd)

    def test_postgres_health_check_retries(self, postgres_compose):
        hc = _services(postgres_compose)["postgres"]["healthcheck"]
        assert hc.get("retries", 0) >= 5

    def test_postgres_volume_defined(self, postgres_compose):
        assert "postgres_storage" in (postgres_compose.get("volumes") or {})

    def test_postgres_mounts_data_volume(self, postgres_compose):
        volumes = _services(postgres_compose)["postgres"].get("volumes", [])
        assert any("postgres_storage" in str(v) for v in volumes)

    def test_postgres_restart_policy(self, postgres_compose):
        restart = _services(postgres_compose)["postgres"].get("restart")
        assert restart == "unless-stopped"

    def test_postgres_uses_ai_stack_network(self, postgres_compose):
        networks = _services(postgres_compose)["postgres"].get("networks", [])
        assert "ai-stack" in networks


# ---------------------------------------------------------------------------
# Qdrant docker-compose
# ---------------------------------------------------------------------------

class TestQdrantCompose:
    def test_qdrant_service_exists(self, qdrant_compose):
        assert "qdrant" in _services(qdrant_compose)

    def test_qdrant_uses_qdrant_image(self, qdrant_compose):
        image = _services(qdrant_compose)["qdrant"].get("image", "")
        assert "qdrant/qdrant" in image

    def test_qdrant_port_6333(self, qdrant_compose):
        ports = _services(qdrant_compose)["qdrant"].get("ports", [])
        assert any("6333" in str(p) for p in ports)

    def test_qdrant_volume_defined(self, qdrant_compose):
        assert "qdrant_storage" in (qdrant_compose.get("volumes") or {})

    def test_qdrant_mounts_storage_volume(self, qdrant_compose):
        volumes = _services(qdrant_compose)["qdrant"].get("volumes", [])
        assert any("qdrant_storage" in str(v) for v in volumes)

    def test_qdrant_restart_policy(self, qdrant_compose):
        restart = _services(qdrant_compose)["qdrant"].get("restart")
        assert restart == "unless-stopped"

    def test_qdrant_uses_ai_stack_network(self, qdrant_compose):
        networks = _services(qdrant_compose)["qdrant"].get("networks", [])
        assert "ai-stack" in networks
