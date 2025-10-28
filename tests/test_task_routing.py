from scripts import poc_local_validate as poc


def test_choose_provider_for_task_calc_prefers_siliconflow(monkeypatch):
    registry = poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml")
    routing = poc.load_yaml(poc.ROOT / "config" / "routing.yaml")
    # 确保无环境变量干扰
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    chosen = poc.choose_provider_for_task(registry, routing, "calc")
    assert chosen in registry["providers"]
    assert chosen == "siliconflow"


def test_choose_provider_for_task_search_prefers_qwen(monkeypatch):
    registry = poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml")
    routing = poc.load_yaml(poc.ROOT / "config" / "routing.yaml")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    chosen = poc.choose_provider_for_task(registry, routing, "search")
    assert chosen in registry["providers"]
    assert chosen == "qwen"

