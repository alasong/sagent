import json
from scripts import poc_local_validate as poc
from scripts import timeline_view as tv


def test_session_jsonl_written(tmp_path, monkeypatch):
    monkeypatch.setattr(poc, "ROOT", tmp_path)
    session_id = "sessABC"
    poc.event_log(session_id, "provider_success", {"provider": "qwen", "duration_ms": 120})
    # 全局日志仍存在
    assert (tmp_path / "logs" / "poc_timeline.log").exists()
    # 会话JSONL存在
    sfile = tmp_path / "logs" / "sessions" / f"{session_id}.jsonl"
    assert sfile.exists()
    content = sfile.read_text(encoding="utf-8").strip().splitlines()
    assert any("provider_success" in line for line in content)


def test_timeline_summary_basic(tmp_path, monkeypatch):
    monkeypatch.setattr(tv, "ROOT", tmp_path)
    sid = "sid1"
    sfile = tmp_path / "logs" / "sessions" / f"{sid}.jsonl"
    sfile.parent.mkdir(parents=True, exist_ok=True)
    events = [
        {"ts": "t1", "session_id": sid, "event": "provider_success", "details": {"provider": "qwen", "duration_ms": 100}},
        {"ts": "t2", "session_id": sid, "event": "provider_failed", "details": {"provider": "moonshot", "reason_code": "policy_latency", "duration_ms": 300}},
        {"ts": "t3", "session_id": sid, "event": "structured_success", "details": {"duration_ms": 200}},
    ]
    with open(sfile, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    loaded = tv.load_session_events(sid, root=tmp_path)
    assert len(loaded) == 3
    summary = tv.summarize_events(loaded)
    assert summary["total_events"] == 3
    assert summary["by_event"].get("provider_success") == 1
    assert summary["by_event"].get("provider_failed") == 1
    assert summary["provider_success_rate"] == 0.5
    lat = summary["latency_ms"]
    assert lat["count"] == 3
    assert isinstance(lat["avg"], float) and isinstance(lat["p50"], float) and isinstance(lat["p95"], float)
