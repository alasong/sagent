import json
from scripts import poc_local_validate as poc


def test_validate_tool_args_calc_schema_valid():
    schema_path = poc.ROOT / "config" / "tools" / "schema" / "calc.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    ok, err = poc.validate_tool_args(schema, {"op": "add", "a": 1, "b": 2})
    assert ok, f"should be valid, got error: {err}"


def test_validate_tool_args_calc_schema_invalid():
    schema_path = poc.ROOT / "config" / "tools" / "schema" / "calc.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    ok, err = poc.validate_tool_args(schema, {"a": 1, "b": 2})
    assert not ok
    assert "'op' is a required property" in err
