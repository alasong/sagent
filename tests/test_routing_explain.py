from scripts.routing_explain import explain_routing
from scripts import poc_local_validate as poc


def test_explain_routing_calc_order():
    info = explain_routing("calc")
    # 根据配置，calc的顺序应以siliconflow开始
    assert isinstance(info["ordered"], list) and len(info["ordered"]) >= 1
    assert info["ordered"][0] == "siliconflow"
    # policies应包含工具级策略的required_capabilities
    assert "required_capabilities" in (info.get("policies") or {})


def test_explain_routing_search_order():
    info = explain_routing("search")
    assert isinstance(info["ordered"], list) and len(info["ordered"]) >= 1
    assert info["ordered"][0] == "qwen"


def test_explain_routing_session_state(tmp_path):
    # 构造一个会话日志：moonshot打开断路器
    session_id = "sess-explain"
    poc.event_log(session_id, "circuit_open", {"provider": "moonshot", "reason": "llm_none"})
    info = explain_routing("calc", session_id=session_id)
    states = (info.get("session") or {}).get("states") or {}
    assert states.get("moonshot", {}).get("state") == "open"
