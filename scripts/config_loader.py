import json
from pathlib import Path
from functools import lru_cache


ROOT = Path(__file__).resolve().parents[1]


def _read_yaml(path: Path):
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def _read_json(path: Path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


class ConfigLoader:
    """Centralized configuration loader with caching and helpers."""

    def __init__(self):
        self._root = ROOT

    @lru_cache(maxsize=1)
    def registry(self) -> dict:
        return _read_yaml(self._root / 'config' / 'models' / 'registry.yaml')

    @lru_cache(maxsize=1)
    def routing(self) -> dict:
        return _read_yaml(self._root / 'config' / 'routing.yaml')

    @lru_cache(maxsize=1)
    def guardrails(self) -> dict:
        return _read_yaml(self._root / 'config' / 'policies' / 'guardrails.yaml')

    @lru_cache(maxsize=1)
    def output_schema(self) -> dict:
        data = _read_json(self._root / 'config' / 'policies' / 'output_schema.json')
        if not data:
            # Fallback default schema
            return {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "citations": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "tool_used": {"type": ["string", "null"]},
                    "tool_result": {}
                },
                "required": ["answer", "citations", "tool_used", "tool_result"],
                "additionalProperties": False
            }
        return data

    def tool_policies(self, tool_name: str) -> dict:
        routing = self.routing() or {}
        # global policies
        pol = (routing.get('policies') or {}).get(tool_name) or {}
        # overlay task_routing.policies if exists
        tr = (routing.get('task_routing') or {})
        tr_policies = (tr.get('policies') or {}).get(tool_name) or {}
        merged = dict(pol)
        merged.update(tr_policies)
        # also include global policies top-level
        global_pol = routing.get('policies') or {}
        for k in ['max_latency_ms', 'max_cost_usd_per_request', 'allow_function_call']:
            if k in global_pol and k not in merged:
                merged[k] = global_pol[k]
        return merged


_LOADER = ConfigLoader()


def get_loader() -> ConfigLoader:
    return _LOADER


def validate_all_configs() -> tuple[bool, list]:
    try:
        from scripts import validate_config as vc
        return vc.validate_all()
    except Exception:
        return False, ["validate_all() not available"]

