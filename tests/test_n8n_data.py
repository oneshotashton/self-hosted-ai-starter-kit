"""Tests for n8n demo workflow and credential data.

Covers:
- JSON validity (handled implicitly by conftest.py fixture loads)
- Required top-level fields in workflow and credential documents
- Correct number and types of workflow nodes
- Correct node types (LangChain chat trigger, LLM chain, Ollama model)
- Node connection wiring (trigger → chain, model → chain)
- Ollama Chat Model references the bundled Ollama credential
- Credential document structure and type tags
- Credential nodesAccess entries match expected node types
"""

import pytest


# ---------------------------------------------------------------------------
# Demo workflow
# ---------------------------------------------------------------------------

class TestDemoWorkflow:
    REQUIRED_FIELDS = ["id", "name", "nodes", "connections", "settings"]

    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_required_field_present(self, field, demo_workflow):
        assert field in demo_workflow, f"Workflow missing required field '{field}'"

    def test_workflow_id(self, demo_workflow):
        assert demo_workflow["id"] == "srOnR8PAY3u4RSwb"

    def test_workflow_name(self, demo_workflow):
        assert demo_workflow["name"] == "Demo workflow"

    def test_workflow_has_three_nodes(self, demo_workflow):
        assert len(demo_workflow["nodes"]) == 3

    def test_workflow_node_names(self, demo_workflow):
        names = {n["name"] for n in demo_workflow["nodes"]}
        assert names == {"Chat Trigger", "Basic LLM Chain", "Ollama Chat Model"}

    def test_chat_trigger_node_type(self, demo_workflow):
        node = next(n for n in demo_workflow["nodes"] if n["name"] == "Chat Trigger")
        assert node["type"] == "@n8n/n8n-nodes-langchain.chatTrigger"

    def test_llm_chain_node_type(self, demo_workflow):
        node = next(n for n in demo_workflow["nodes"] if n["name"] == "Basic LLM Chain")
        assert node["type"] == "@n8n/n8n-nodes-langchain.chainLlm"

    def test_ollama_chat_model_node_type(self, demo_workflow):
        node = next(n for n in demo_workflow["nodes"] if n["name"] == "Ollama Chat Model")
        assert node["type"] == "@n8n/n8n-nodes-langchain.lmChatOllama"

    def test_ollama_model_parameter(self, demo_workflow):
        node = next(n for n in demo_workflow["nodes"] if n["name"] == "Ollama Chat Model")
        assert node["parameters"]["model"] == "llama3.2:latest"

    def test_ollama_node_references_credential(self, demo_workflow):
        node = next(n for n in demo_workflow["nodes"] if n["name"] == "Ollama Chat Model")
        creds = node.get("credentials", {})
        assert "ollamaApi" in creds, "Ollama Chat Model must reference an ollamaApi credential"

    def test_ollama_credential_id_matches_bundled_file(self, demo_workflow, ollama_credential):
        node = next(n for n in demo_workflow["nodes"] if n["name"] == "Ollama Chat Model")
        ref_id = node["credentials"]["ollamaApi"]["id"]
        assert ref_id == ollama_credential["id"], (
            "Workflow references credential ID that does not match bundled credential file"
        )

    def test_ollama_credential_name_in_workflow(self, demo_workflow):
        node = next(n for n in demo_workflow["nodes"] if n["name"] == "Ollama Chat Model")
        name = node["credentials"]["ollamaApi"].get("name", "")
        assert name != "", "Credential reference in workflow must include a name"

    def test_chat_trigger_connects_to_llm_chain(self, demo_workflow):
        connections = demo_workflow["connections"]
        assert "Chat Trigger" in connections, "Chat Trigger must have outbound connections"
        main_outputs = connections["Chat Trigger"].get("main", [])
        targets = [conn["node"] for outputs in main_outputs for conn in outputs]
        assert "Basic LLM Chain" in targets

    def test_ollama_model_connects_to_llm_chain(self, demo_workflow):
        connections = demo_workflow["connections"]
        assert "Ollama Chat Model" in connections
        ai_outputs = connections["Ollama Chat Model"].get("ai_languageModel", [])
        targets = [conn["node"] for outputs in ai_outputs for conn in outputs]
        assert "Basic LLM Chain" in targets

    def test_workflow_settings_has_execution_order(self, demo_workflow):
        assert demo_workflow["settings"].get("executionOrder") == "v1"

    def test_workflow_meta_template_creds_completed(self, demo_workflow):
        meta = demo_workflow.get("meta") or {}
        assert meta.get("templateCredsSetupCompleted") is True

    def test_each_node_has_unique_id(self, demo_workflow):
        ids = [n["id"] for n in demo_workflow["nodes"]]
        assert len(ids) == len(set(ids)), "Each node must have a unique ID"

    def test_each_node_has_position(self, demo_workflow):
        for node in demo_workflow["nodes"]:
            pos = node.get("position", [])
            assert len(pos) == 2, f"Node '{node['name']}' missing valid position"


# ---------------------------------------------------------------------------
# Ollama API credential
# ---------------------------------------------------------------------------

class TestOllamaCredential:
    REQUIRED_FIELDS = ["id", "name", "data", "type", "nodesAccess"]

    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_required_field_present(self, field, ollama_credential):
        assert field in ollama_credential, f"Ollama credential missing field '{field}'"

    def test_credential_id(self, ollama_credential):
        assert ollama_credential["id"] == "xHuYe0MDGOs9IpBW"

    def test_credential_type_is_ollama_api(self, ollama_credential):
        assert ollama_credential["type"] == "ollamaApi"

    def test_credential_name(self, ollama_credential):
        assert ollama_credential["name"] == "Local Ollama service"

    def test_credential_data_is_non_empty(self, ollama_credential):
        assert ollama_credential["data"] != ""

    def test_nodes_access_is_list(self, ollama_credential):
        assert isinstance(ollama_credential["nodesAccess"], list)

    def test_nodes_access_contains_chat_ollama(self, ollama_credential):
        node_types = [entry["nodeType"] for entry in ollama_credential["nodesAccess"]]
        assert "@n8n/n8n-nodes-langchain.lmChatOllama" in node_types

    def test_nodes_access_contains_lm_ollama(self, ollama_credential):
        node_types = [entry["nodeType"] for entry in ollama_credential["nodesAccess"]]
        assert "@n8n/n8n-nodes-langchain.lmOllama" in node_types


# ---------------------------------------------------------------------------
# Qdrant API credential
# ---------------------------------------------------------------------------

class TestQdrantCredential:
    REQUIRED_FIELDS = ["id", "name", "data", "type", "nodesAccess"]

    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_required_field_present(self, field, qdrant_credential):
        assert field in qdrant_credential, f"Qdrant credential missing field '{field}'"

    def test_credential_id(self, qdrant_credential):
        assert qdrant_credential["id"] == "sFfERYppMeBnFNeA"

    def test_credential_type_is_qdrant_api(self, qdrant_credential):
        assert qdrant_credential["type"] == "qdrantApi"

    def test_credential_name(self, qdrant_credential):
        assert qdrant_credential["name"] == "Local QdrantApi database"

    def test_credential_data_is_non_empty(self, qdrant_credential):
        assert qdrant_credential["data"] != ""

    def test_nodes_access_is_list(self, qdrant_credential):
        assert isinstance(qdrant_credential["nodesAccess"], list)

    def test_nodes_access_contains_vector_store_qdrant(self, qdrant_credential):
        node_types = [entry["nodeType"] for entry in qdrant_credential["nodesAccess"]]
        assert "@n8n/n8n-nodes-langchain.vectorStoreQdrant" in node_types
