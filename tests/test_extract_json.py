from scripts import poc_local_validate as poc


def test_extract_json_simple_block():
    text = """
    一些描述...
    ```json
    {"answer": "ok", "citations": ["ref"], "tool_used": "none", "tool_result": null}
    ```
    结尾。
    """
    data = poc.extract_json(text)
    assert isinstance(data, dict)
    assert data.get("answer") == "ok"
    assert data.get("citations") == ["ref"]


def test_extract_json_invalid_returns_none():
    text = "没有json块的文本"
    data = poc.extract_json(text)
    assert data is None

