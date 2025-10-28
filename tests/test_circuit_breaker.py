import json
import time
from scripts import poc_local_validate as poc


def make_registry():
    return {
        "providers": {
            "p1": {"model": "m1"},
            "p2": {"model": "m2"},
        }
    }


def make_policies(tmp_path, threshold=1, cooldown=5):
    routing = {
        "policies": {
            "circuit_breaker": {"failure_threshold": threshold, "cooldown_seconds": cooldown}
        }
    }
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    with open(tmp_path / "config" / "routing.yaml", "w", encoding="utf-8") as f:
        import yaml
        yaml.safe_dump(routing, f, allow_unicode=True, sort_keys=False)


def test_circuit_opens_after_threshold_and_skips(tmp_path, monkeypatch):
    # 路由策略：阈值1、冷却5s
    monkeypatch.setattr(poc, "ROOT", tmp_path)
    make_policies(tmp_path, threshold=1, cooldown=5)
    registry = make_registry()

    # 第一次：p1返回None（失败），p2返回成功JSON
    def fake_llm(system_prompt, user_prompt, model_name, cfg, logger=None):
        if model_name == "m1":
            return None
        return json.dumps({
            "answer": "ok",
            "citations": ["ref"],
            "tool_used": "none",
            "tool_result": None
        }, ensure_ascii=False)

    monkeypatch.setattr(poc, "llm_text", fake_llm)

    ordered = ["p1", "p2"]
    out, provider, model, tried = poc.structured_answer_with_failover(
        ordered, registry, user_prompt="q", citation="ref", tool_used=None, tool_result=None, schema=poc.load_output_schema(), logger=None, session_id=None
    )
    assert out is not None and provider == "p2"
    # p1应当打开断路器
    st = poc.CIRCUIT_STATE.get("p1")
    assert st and st["state"] == "open"

    # 第二次调用：由于冷却未过，应跳过p1（skip_circuit_open）并直接尝试p2
    out2, provider2, model2, tried2 = poc.structured_answer_with_failover(
        ordered, registry, user_prompt="q", citation="ref", tool_used=None, tool_result=None, schema=poc.load_output_schema(), logger=None, session_id=None
    )
    assert out2 is not None and provider2 == "p2"
    assert any(t.startswith("skip_circuit_open:") for t in tried2)


def test_circuit_half_open_recovery(tmp_path, monkeypatch):
    # 阈值1、冷却0.1s，p1先失败导致open，然后冷却过后半开并成功关闭
    monkeypatch.setattr(poc, "ROOT", tmp_path)
    make_policies(tmp_path, threshold=1, cooldown=0.1)
    registry = make_registry()

    # 第一次：p1失败，p2成功
    def fake_llm(system_prompt, user_prompt, model_name, cfg, logger=None):
        if model_name == "m1":
            return None
        return json.dumps({
            "answer": "ok",
            "citations": ["ref"],
            "tool_used": "none",
            "tool_result": None
        }, ensure_ascii=False)

    monkeypatch.setattr(poc, "llm_text", fake_llm)
    ordered = ["p1", "p2"]
    out, provider, model, tried = poc.structured_answer_with_failover(
        ordered, registry, user_prompt="q", citation="ref", tool_used=None, tool_result=None, schema=poc.load_output_schema(), logger=None, session_id=None
    )
    assert poc.CIRCUIT_STATE.get("p1", {}).get("state") == "open"

    # 模拟冷却过期：直接调整opened_at到过去
    poc.CIRCUIT_STATE["p1"]["opened_at"] = time.monotonic() - 1.0

    # 半开尝试：此时让p1成功返回
    def fake_llm2(system_prompt, user_prompt, model_name, cfg, logger=None):
        return json.dumps({
            "answer": "ok",
            "citations": ["ref"],
            "tool_used": "none",
            "tool_result": None
        }, ensure_ascii=False)

    monkeypatch.setattr(poc, "llm_text", fake_llm2)
    out2, provider2, model2, tried2 = poc.structured_answer_with_failover(
        ordered, registry, user_prompt="q", citation="ref", tool_used=None, tool_result=None, schema=poc.load_output_schema(), logger=None, session_id=None
    )
    # p1应当在半开成功后关闭
    st = poc.CIRCUIT_STATE.get("p1")
    assert st and st["state"] == "closed" and st["failures"] == 0
