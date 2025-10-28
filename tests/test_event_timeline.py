from scripts import poc_local_validate as poc


def test_event_log_writes_json_line(tmp_path, monkeypatch):
    # 重定向日志目录到临时路径
    logs_dir = tmp_path / "logs"
    monkeypatch.setattr(poc, "ROOT", tmp_path)
    session_id = "sess123"
    poc.event_log(session_id, "test_event", {"k": "v"})
    timeline = logs_dir / "poc_timeline.log"
    assert timeline.exists()
    content = timeline.read_text(encoding="utf-8").strip()
    assert "\n" not in content or content.endswith("\n")
    assert "test_event" in content and "sess123" in content

