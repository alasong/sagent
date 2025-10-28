import json
from scripts import poc_local_validate as poc


def test_sla_total_timeout_skips_all(tmp_path, monkeypatch):
    # 配置全局SLA总时延为0ms，确保任何流程都会超时
    routing = {
        "policies": {"max_latency_ms_total": 0}
    }
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    with open(tmp_path / "config" / "routing.yaml", "w", encoding="utf-8") as f:
        import yaml
        yaml.safe_dump(routing, f, allow_unicode=True, sort_keys=False)

    # 使用临时ROOT以读取上述策略
    monkeypatch.setattr(poc, "ROOT", tmp_path)

    # 构造两个提供方，但由于SLA总时延为0，应当在尝试前就终止
    registry = {
        "providers": {
            "p1": {"model": "m1"},
            "p2": {"model": "m2"},
        }
    }

    # mock llm_text：若被调用，返回合法JSON（但期望不会调用到）
    def fake_llm(system_prompt, user_prompt, model_name, cfg, logger=None):
        return json.dumps({
            "answer": "ok",
            "citations": ["ref"],
            "tool_used": "none",
            "tool_result": None
        }, ensure_ascii=False)

    monkeypatch.setattr(poc, "llm_text", fake_llm)

    session_id = "sess-sla0"
    ordered = ["p1", "p2"]
    out, provider, model, tried = poc.structured_answer_with_failover(
        ordered, registry, user_prompt="q", citation="ref", tool_used=None, tool_result=None, schema=poc.load_output_schema(), logger=None, session_id=session_id
    )
    # 应未产生输出，且标记包含sla_timeout_total
    assert out is None and provider is None
    assert "sla_timeout_total" in tried

    # 检查会话日志中记录了sla超时事件
    log_file = tmp_path / "logs" / "sessions" / f"{session_id}.jsonl"
    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert any("\"event\": \"sla_timeout_total\"" in l for l in lines)

