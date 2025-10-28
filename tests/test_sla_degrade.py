import json
from scripts import poc_local_validate as poc


def test_sla_degrade_returns_offline_output(tmp_path, monkeypatch):
    routing = {
        "policies": {"max_latency_ms_total": 0, "on_sla_timeout": "degrade"}
    }
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    with open(tmp_path / "config" / "routing.yaml", "w", encoding="utf-8") as f:
        import yaml
        yaml.safe_dump(routing, f, allow_unicode=True, sort_keys=False)
    monkeypatch.setattr(poc, "ROOT", tmp_path)

    registry = {"providers": {"p1": {"model": "m1"}, "p2": {"model": "m2"}}}

    # 若被调用，返回合法JSON（但总时延为0应不调用）
    def fake_llm(system_prompt, user_prompt, model_name, cfg, logger=None):
        return json.dumps({
            "answer": "ok",
            "citations": ["ref"],
            "tool_used": "none",
            "tool_result": None
        }, ensure_ascii=False)
    monkeypatch.setattr(poc, "llm_text", fake_llm)

    session_id = "sess-degrade"
    out, provider, model, tried = poc.structured_answer_with_failover(
        ["p1", "p2"], registry, user_prompt="q", citation="ref", tool_used="calc", tool_result={"result": 46.0}, schema=poc.load_output_schema(), logger=None, session_id=session_id
    )
    assert out is not None and provider is None and model is None
    assert "sla_timeout_total" in tried and "sla_degrade" in tried
    # 字段完整
    assert set(out.keys()) == {"answer", "citations", "tool_used", "tool_result"}
    # 事件存在
    log_file = tmp_path / "logs" / "sessions" / f"{session_id}.jsonl"
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert any("\"event\": \"sla_degrade_total\"" in l for l in lines)


def test_sla_abort_returns_none(tmp_path, monkeypatch):
    routing = {
        "policies": {"max_latency_ms_total": 0, "on_sla_timeout": "abort"}
    }
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    with open(tmp_path / "config" / "routing.yaml", "w", encoding="utf-8") as f:
        import yaml
        yaml.safe_dump(routing, f, allow_unicode=True, sort_keys=False)
    monkeypatch.setattr(poc, "ROOT", tmp_path)

    registry = {"providers": {"p1": {"model": "m1"}, "p2": {"model": "m2"}}}
    def fake_llm(system_prompt, user_prompt, model_name, cfg, logger=None):
        return json.dumps({
            "answer": "ok",
            "citations": ["ref"],
            "tool_used": "none",
            "tool_result": None
        }, ensure_ascii=False)
    monkeypatch.setattr(poc, "llm_text", fake_llm)

    session_id = "sess-abort"
    out, provider, model, tried = poc.structured_answer_with_failover(
        ["p1", "p2"], registry, user_prompt="q", citation="ref", tool_used=None, tool_result=None, schema=poc.load_output_schema(), logger=None, session_id=session_id
    )
    assert out is None and provider is None and model is None
    assert "sla_timeout_total" in tried and "sla_degrade" not in tried
    log_file = tmp_path / "logs" / "sessions" / f"{session_id}.jsonl"
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert any("\"event\": \"sla_timeout_total\"" in l for l in lines)

