import os
import copy
from scripts import poc_local_validate as poc


def test_choose_provider_weighted_prefers_qwen(monkeypatch):
    registry = poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml")
    routing = poc.load_yaml(poc.ROOT / "config" / "routing.yaml")
    # 确保无环境变量干扰
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    chosen = poc.choose_provider(registry, routing)
    assert chosen in registry["providers"], "provider must exist in registry"
    # 当前权重最高为qwen
    assert chosen == "qwen"


def test_choose_provider_env_override(monkeypatch):
    registry = poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml")
    # 如果注册里有baidu，则设置环境变量应优先
    if "baidu" in registry["providers"]:
        monkeypatch.setenv("LLM_PROVIDER", "baidu")
        routing = {"strategy": {"type": "weighted", "weights": {"qwen": 1.0}}}
        chosen = poc.choose_provider(registry, routing)
        assert chosen == "baidu"


def test_choose_provider_env_override_moonshot(monkeypatch):
    registry = poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml")
    if "moonshot" in registry["providers"]:
        monkeypatch.setenv("LLM_PROVIDER", "moonshot")
        routing = {"strategy": {"type": "weighted", "weights": {"qwen": 1.0}}}
        chosen = poc.choose_provider(registry, routing)
        assert chosen == "moonshot"


def test_choose_provider_env_override_siliconflow(monkeypatch):
    registry = poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml")
    if "siliconflow" in registry["providers"]:
        monkeypatch.setenv("LLM_PROVIDER", "siliconflow")
        routing = {"strategy": {"type": "weighted", "weights": {"qwen": 1.0}}}
        chosen = poc.choose_provider(registry, routing)
        assert chosen == "siliconflow"

