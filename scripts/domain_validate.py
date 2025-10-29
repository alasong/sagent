import json
from pathlib import Path
from typing import Dict, Any, Tuple

from jsonschema import validate as jsonschema_validate, ValidationError

ROOT = Path(__file__).resolve().parents[1]


def load_domain_schema(domain: str) -> Dict[str, Any]:
    path = ROOT / "config" / "domain_schema" / f"{domain}.json"
    if not path.exists():
        raise FileNotFoundError(f"unknown domain schema: {domain}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_domain(doc: Any, domain: str) -> Tuple[bool, str | None]:
    try:
        schema = load_domain_schema(domain)
        jsonschema_validate(instance=doc, schema=schema)
        # Additional lightweight consistency checks
        if domain == "stories":
            # Each story should have non-empty acceptance criteria
            for i, story in enumerate(doc or []):
                ac = story.get("acceptance_criteria") if isinstance(story, dict) else None
                if not ac or not isinstance(ac, list) or len(ac) == 0:
                    return False, f"story[{i}] missing acceptance_criteria"
        if domain == "prd":
            # Features should have unique IDs
            feats = (doc.get("features") or []) if isinstance(doc, dict) else []
            ids = [f.get("id") for f in feats if isinstance(f, dict)]
            if len(ids) != len(set(ids)):
                return False, "features contain duplicate ids"
        return True, None
    except ValidationError as e:
        return False, str(e)
    except Exception as e:
        return False, f"validation failed: {e}"


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Validate domain-specific documents against JSON Schemas")
    ap.add_argument("--domain", required=True, help="Domain name, e.g., prd/stories/nfr/risks/dependencies/acceptance")
    ap.add_argument("--file", required=True, help="Path to JSON document to validate")
    args = ap.parse_args()
    payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
    ok, err = validate_domain(payload, args.domain)
    print(json.dumps({"ok": ok, "error": err}, ensure_ascii=False))


if __name__ == "__main__":
    main()

