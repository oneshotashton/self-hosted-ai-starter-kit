"""Tests for .env.example configuration files.

Covers:
- File presence for all env examples
- Required environment variables in each file
- No empty values in example files (i.e., every var has a placeholder)
- Consistency of shared variables across root and service-level examples
"""

import pathlib
import re
import pytest


REPO_ROOT = pathlib.Path(__file__).parent.parent


def parse_env_file(path: pathlib.Path) -> dict[str, str]:
    """Parse a .env / .env.example file into a {key: value} dict.

    Skips blank lines and comment lines. Inline comments are stripped.
    """
    result = {}
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        # Strip inline comments (e.g.  PASS=secret  # comment)
        value = re.sub(r"\s*#.*$", "", value).strip()
        result[key.strip()] = value
    return result


ENV_FILES = {
    "root": REPO_ROOT / ".env.example",
    "n8n": REPO_ROOT / "n8n" / ".env.example",
    "postgres": REPO_ROOT / "postgres" / ".env.example",
}


# ---------------------------------------------------------------------------
# File presence
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("label,path", list(ENV_FILES.items()))
def test_env_example_exists(label, path):
    assert path.exists(), f".env.example not found for {label}: {path}"


# ---------------------------------------------------------------------------
# Root .env.example
# ---------------------------------------------------------------------------

class TestRootEnvExample:
    REQUIRED_VARS = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "N8N_ENCRYPTION_KEY",
        "N8N_USER_MANAGEMENT_JWT_SECRET",
        "N8N_DEFAULT_BINARY_DATA_MODE",
    ]

    @pytest.fixture(scope="class")
    def root_env(self):
        return parse_env_file(ENV_FILES["root"])

    @pytest.mark.parametrize("var", REQUIRED_VARS)
    def test_required_var_present(self, var, root_env):
        assert var in root_env, f"'{var}' missing from root .env.example"

    @pytest.mark.parametrize("var", REQUIRED_VARS)
    def test_required_var_has_value(self, var, root_env):
        assert root_env[var] != "", f"'{var}' has empty value in root .env.example"

    def test_postgres_user_default(self, root_env):
        assert root_env["POSTGRES_USER"] == "root"

    def test_postgres_db_default(self, root_env):
        assert root_env["POSTGRES_DB"] == "n8n"

    def test_binary_data_mode_default(self, root_env):
        assert root_env["N8N_DEFAULT_BINARY_DATA_MODE"] == "filesystem"


# ---------------------------------------------------------------------------
# n8n .env.example
# ---------------------------------------------------------------------------

class TestN8nEnvExample:
    REQUIRED_VARS = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "N8N_ENCRYPTION_KEY",
        "N8N_USER_MANAGEMENT_JWT_SECRET",
        "N8N_RUNNERS_AUTH_TOKEN",
    ]

    @pytest.fixture(scope="class")
    def n8n_env(self):
        return parse_env_file(ENV_FILES["n8n"])

    @pytest.mark.parametrize("var", REQUIRED_VARS)
    def test_required_var_present(self, var, n8n_env):
        assert var in n8n_env, f"'{var}' missing from n8n .env.example"

    @pytest.mark.parametrize("var", REQUIRED_VARS)
    def test_required_var_has_value(self, var, n8n_env):
        assert n8n_env[var] != "", f"'{var}' has empty value in n8n .env.example"

    def test_postgres_user_default(self, n8n_env):
        assert n8n_env["POSTGRES_USER"] == "root"

    def test_postgres_db_default(self, n8n_env):
        assert n8n_env["POSTGRES_DB"] == "n8n"

    def test_runners_auth_token_has_value(self, n8n_env):
        assert n8n_env["N8N_RUNNERS_AUTH_TOKEN"] != ""


# ---------------------------------------------------------------------------
# postgres .env.example
# ---------------------------------------------------------------------------

class TestPostgresEnvExample:
    REQUIRED_VARS = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
    ]

    @pytest.fixture(scope="class")
    def pg_env(self):
        return parse_env_file(ENV_FILES["postgres"])

    @pytest.mark.parametrize("var", REQUIRED_VARS)
    def test_required_var_present(self, var, pg_env):
        assert var in pg_env, f"'{var}' missing from postgres .env.example"

    @pytest.mark.parametrize("var", REQUIRED_VARS)
    def test_required_var_has_value(self, var, pg_env):
        assert pg_env[var] != "", f"'{var}' has empty value in postgres .env.example"

    def test_postgres_user_default(self, pg_env):
        assert pg_env["POSTGRES_USER"] == "root"

    def test_postgres_db_default(self, pg_env):
        assert pg_env["POSTGRES_DB"] == "n8n"


# ---------------------------------------------------------------------------
# Cross-file consistency: shared PostgreSQL credentials
# ---------------------------------------------------------------------------

class TestEnvCrossFileConsistency:
    """Shared PostgreSQL variables must have the same defaults across all files."""

    SHARED_POSTGRES_VARS = ["POSTGRES_USER", "POSTGRES_DB"]

    @pytest.fixture(scope="class")
    def all_envs(self):
        return {label: parse_env_file(path) for label, path in ENV_FILES.items()}

    @pytest.mark.parametrize("var", SHARED_POSTGRES_VARS)
    def test_shared_var_consistent_across_files(self, var, all_envs):
        values = {label: env[var] for label, env in all_envs.items() if var in env}
        unique_values = set(values.values())
        assert len(unique_values) == 1, (
            f"'{var}' has inconsistent defaults across env files: {values}"
        )

    def test_encryption_key_present_in_root_and_n8n(self, all_envs):
        assert "N8N_ENCRYPTION_KEY" in all_envs["root"]
        assert "N8N_ENCRYPTION_KEY" in all_envs["n8n"]

    def test_jwt_secret_present_in_root_and_n8n(self, all_envs):
        assert "N8N_USER_MANAGEMENT_JWT_SECRET" in all_envs["root"]
        assert "N8N_USER_MANAGEMENT_JWT_SECRET" in all_envs["n8n"]
