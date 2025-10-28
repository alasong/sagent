from scripts import poc_local_validate as poc
from scripts.routing_explain import explain_routing
import json


def test_web_fetch_schema_valid():
    schema_path = poc.ROOT / "config" / "tools" / "schema" / "web_fetch.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    ok, err = poc.validate_tool_args(schema, {"url": "https://example.com", "method": "GET"})
    assert ok, f"schema should be valid: {err}"


def test_file_read_schema_valid():
    schema_path = poc.ROOT / "config" / "tools" / "schema" / "file_read.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    ok, err = poc.validate_tool_args(schema, {"path": str(poc.ROOT / "data" / "docs" / "sample_knowledge.txt")})
    assert ok, f"schema should be valid: {err}"


def test_routing_explain_includes_web_fetch():
    info = explain_routing("web_fetch")
    assert "ordered" in info and isinstance(info["ordered"], list)
    assert len(info["ordered"]) > 0
    assert set(info["ordered"]).issubset(set((poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml").get("providers") or {}).keys()))
