"""Shared fixtures for the test suite."""

import pathlib
import json
import pytest
import yaml


REPO_ROOT = pathlib.Path(__file__).parent.parent


def load_yaml(path: pathlib.Path) -> dict:
    """Parse a YAML file and return the document as a dict."""
    with path.open() as fh:
        return yaml.safe_load(fh)


def load_json(path: pathlib.Path) -> dict:
    """Parse a JSON file and return the document as a dict."""
    with path.open() as fh:
        return json.load(fh)


@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT


@pytest.fixture(scope="session")
def root_compose(repo_root):
    return load_yaml(repo_root / "docker-compose.yml")


@pytest.fixture(scope="session")
def n8n_compose(repo_root):
    return load_yaml(repo_root / "n8n" / "docker-compose.yml")


@pytest.fixture(scope="session")
def ollama_compose(repo_root):
    return load_yaml(repo_root / "ollama" / "docker-compose.yml")


@pytest.fixture(scope="session")
def postgres_compose(repo_root):
    return load_yaml(repo_root / "postgres" / "docker-compose.yml")


@pytest.fixture(scope="session")
def qdrant_compose(repo_root):
    return load_yaml(repo_root / "qdrant" / "docker-compose.yml")


@pytest.fixture(scope="session")
def demo_workflow(repo_root):
    return load_json(
        repo_root / "n8n" / "demo-data" / "workflows" / "srOnR8PAY3u4RSwb.json"
    )


@pytest.fixture(scope="session")
def ollama_credential(repo_root):
    return load_json(
        repo_root / "n8n" / "demo-data" / "credentials" / "xHuYe0MDGOs9IpBW.json"
    )


@pytest.fixture(scope="session")
def qdrant_credential(repo_root):
    return load_json(
        repo_root / "n8n" / "demo-data" / "credentials" / "sFfERYppMeBnFNeA.json"
    )
