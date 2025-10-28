import json
from scripts import poc_local_validate as poc


def test_ask_structured_answer_retry_fixes_missing_citation(monkeypatch):
    # 第一次返回缺少citation，第二次返回包含citation
    responses = [
        json.dumps({
            "answer": "结果为46",
            "citations": [],
            "tool_used": "calc",
            "tool_result": {"result": 46.0}
        }, ensure_ascii=False),
        json.dumps({
            "answer": "结果为46",
            "citations": ["参考语句"],
            "tool_used": "calc",
            "tool_result": {"result": 46.0}
        }, ensure_ascii=False),
    ]

    def fake_llm(system_prompt, user_prompt, model_name, cfg, logger=None):
        return responses.pop(0)

    monkeypatch.setattr(poc, "llm_text", fake_llm)

    schema = poc.load_output_schema()
    out = poc.ask_structured_answer(
        model_name="dummy",
        cfg={},
        user_prompt="计算",
        citation="参考语句",
        tool_used="calc",
        tool_result={"result": 46.0},
        schema=schema,
        max_retries=2,
        logger=None,
    )
    assert out is not None
    assert isinstance(out.get("citations"), list) and len(out["citations"]) >= 1

