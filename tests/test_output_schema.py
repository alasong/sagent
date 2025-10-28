from scripts import poc_local_validate as poc


def test_load_output_schema():
    schema = poc.load_output_schema()
    assert isinstance(schema, dict)
    assert set(["answer", "citations"]).issubset(schema.get("properties", {}).keys())

