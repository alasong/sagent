from scripts import poc_local_validate as poc


def test_tool_level_fallback_used_when_by_tool_missing(monkeypatch):
    # 构造路由：没有 by_tool，但有工具级 fallback_chain
    routing = {
        "fallback_chain": ["baidu", "qwen"],  # 全局链（不会被使用）
        "task_routing": {
            "fallback_chain": {
                "calc": ["moonshot", "qwen", "siliconflow"],
            }
        }
    }
    registry = poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml")
    order = poc.select_providers_for_tool(registry, routing, "calc")
    # 应优先使用工具级fallback_chain顺序
    assert order[:2] == ["moonshot", "qwen"]
    # 所有返回项都应存在于注册表
    providers = set((registry.get("providers") or {}).keys())
    assert all(p in providers for p in order)


def test_by_tool_takes_precedence_over_tool_fallback(monkeypatch):
    # 同时定义 by_tool 与 tool fallback，by_tool 应优先
    routing = {
        "task_routing": {
            "by_tool": {
                "search": ["qwen", "moonshot"]
            },
            "fallback_chain": {
                "search": ["moonshot", "siliconflow", "qwen"]
            }
        }
    }
    registry = poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml")
    order = poc.select_providers_for_tool(registry, routing, "search")
    # 应优先返回 by_tool 的列表
    assert order[:2] == ["qwen", "moonshot"]
    providers = set((registry.get("providers") or {}).keys())
    assert all(p in providers for p in order)

