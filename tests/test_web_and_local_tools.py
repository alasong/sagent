from scripts import poc_local_validate as poc
from scripts.routing_explain import explain_routing
import json


def test_web_search_schema_valid():
    schema_path = poc.ROOT / "config" / "tools" / "schema" / "web_search.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    ok, err = poc.validate_tool_args(schema, {"query": "site:example.com", "limit": 3, "source": "duckduckgo"})
    assert ok, f"schema should be valid: {err}"


def test_run_command_schema_valid():
    schema_path = poc.ROOT / "config" / "tools" / "schema" / "run_command.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    ok, err = poc.validate_tool_args(schema, {"command": "echo", "args": ["hello"], "timeout_seconds": 5})
    assert ok, f"schema should be valid: {err}"


def test_routing_explain_includes_web_search():
    info = explain_routing("web_search")
    assert "ordered" in info and isinstance(info["ordered"], list)
    assert len(info["ordered"]) > 0
    assert set(info["ordered"]).issubset(set((poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml").get("providers") or {}).keys()))

