from pathlib import Path
from scripts import validate_config as vc


def write_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    import yaml
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def test_valid_config_passes(tmp_path, monkeypatch):
    # Prepare minimal valid config
    monkeypatch.setattr(vc, "ROOT", tmp_path)
    reg = {
        "providers": {
            "qwen": {"model": "qwen-turbo", "capabilities": ["function_call", "long_context"]},
            "moonshot": {"model": "moonshot-v1-8k", "capabilities": ["function_call", "long_context"]},
        },
        "default_provider": "qwen",
    }
    routing = {
        "strategy": {"type": "weighted", "weights": {"qwen": 0.8}},
        "fallback_chain": ["qwen"],
        "policies": {"max_latency_ms": 6000, "max_cost_usd_per_request": 0.05},
        "task_routing": {
            "by_tool": {"search": ["qwen", "moonshot"]},
            "fallback_chain": {"search": ["moonshot", "qwen"]},
            "policies": {"search": {"required_capabilities": ["long_context"]}},
        },
    }
    write_yaml(tmp_path / "config" / "models" / "registry.yaml", reg)
    write_yaml(tmp_path / "config" / "routing.yaml", routing)
    ok, issues = vc.validate_all()
    assert ok, f"expected ok, issues: {issues}"


def test_invalid_provider_reference_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "ROOT", tmp_path)
    reg = {
        "providers": {
            "qwen": {"model": "qwen-turbo", "capabilities": ["function_call", "long_context"]},
        },
    }
    routing = {
        "task_routing": {"by_tool": {"calc": ["moonshot"]}},
    }
    write_yaml(tmp_path / "config" / "models" / "registry.yaml", reg)
    write_yaml(tmp_path / "config" / "routing.yaml", routing)
    ok, issues = vc.validate_all()
    assert not ok
    assert any("unknown providers" in i.get("message", "") for i in issues)


def test_required_capabilities_no_candidate_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "ROOT", tmp_path)
    reg = {
        "providers": {
            "a": {"model": "a-model", "capabilities": ["function_call"]},
            "b": {"model": "b-model", "capabilities": ["function_call"]},
        },
    }
    routing = {
        "task_routing": {
            "by_tool": {"search": ["a", "b"]},
            "policies": {"search": {"required_capabilities": ["long_context"]}},
        }
    }
    write_yaml(tmp_path / "config" / "models" / "registry.yaml", reg)
    write_yaml(tmp_path / "config" / "routing.yaml", routing)
    ok, issues = vc.validate_all()
    assert not ok
    assert any("required_capabilities" in i.get("message", "") for i in issues)


def test_strategy_weights_checks(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "ROOT", tmp_path)
    reg = {"providers": {"p1": {"model": "m1"}, "p2": {"model": "m2"}}}
    routing = {"strategy": {"type": "weighted", "weights": {"p1": 0.8, "p2": 0.5}}}
    write_yaml(tmp_path / "config" / "models" / "registry.yaml", reg)
    write_yaml(tmp_path / "config" / "routing.yaml", routing)
    ok, issues = vc.validate_all()
    # sum != 1.0 yields a warning, but still ok
    assert ok
    assert any("weights sum" in i.get("message", "") and i.get("severity") == "warning" for i in issues)


def test_tool_schema_without_routing_warns(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "ROOT", tmp_path)
    reg = {"providers": {"qwen": {"model": "qwen-turbo"}}}
    routing = {}
    # create a tool schema file
    tools_dir = tmp_path / "config" / "tools" / "schema"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "calc.json").write_text("{}", encoding="utf-8")
    write_yaml(tmp_path / "config" / "models" / "registry.yaml", reg)
    write_yaml(tmp_path / "config" / "routing.yaml", routing)
    ok, issues = vc.validate_all()
    assert ok
    assert any("has schema but no routing" in i.get("message", "") for i in issues)


def test_routing_unknown_tool_warns(tmp_path, monkeypatch):
    monkeypatch.setattr(vc, "ROOT", tmp_path)
    reg = {"providers": {"q": {"model": "m"}}}
    routing = {"task_routing": {"by_tool": {"not_exist": ["q"]}}}
    # ensure tools schema directory exists (empty)
    (tmp_path / "config" / "tools" / "schema").mkdir(parents=True, exist_ok=True)
    write_yaml(tmp_path / "config" / "models" / "registry.yaml", reg)
    write_yaml(tmp_path / "config" / "routing.yaml", routing)
    ok, issues = vc.validate_all()
    assert ok
    assert any("without a schema file" in i.get("message", "") for i in issues)
