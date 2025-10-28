import json
from scripts import poc_local_validate as poc


def test_structured_answer_with_failover_uses_second_provider(monkeypatch):
    registry = poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml")
    # 构造尝试顺序：先siliconflow再moonshot
    ordered = [p for p in ["siliconflow", "moonshot"] if p in registry["providers"]]
    assert len(ordered) >= 2

    def fake_llm(system_prompt, user_prompt, model_name, cfg, logger=None):
        # siliconflow返回None，moonshot返回合法JSON
        if cfg.get("api_key_env") == "SILICONFLOW_API_KEY":
            return None
        return json.dumps({
            "answer": "结果为46",
            "citations": ["参考"],
            "tool_used": "calc",
            "tool_result": {"result": 46.0}
        }, ensure_ascii=False)

    monkeypatch.setattr(poc, "llm_text", fake_llm)

    out, provider, model, tried = poc.structured_answer_with_failover(
        ordered,
        registry,
        user_prompt="计算",
        citation="参考",
        tool_used="calc",
        tool_result={"result": 46.0},
        schema=poc.load_output_schema(),
        logger=None,
    )
    assert out is not None
    assert provider == "moonshot"
    assert "siliconflow" in tried
    assert "moonshot" in tried


def test_policy_allows_provider_cost_filter():
    policies = {"max_cost_usd_per_request": 0.000001}
    cfg = {"cost": {"input_per_1k_tokens_usd": 0.1, "output_per_1k_tokens_usd": 0.1}}
    allowed = poc.policy_allows_provider(cfg, policies, est_tokens=1000)
    assert allowed is False

