import sys
import json
from pathlib import Path
from typing import Tuple, List, Dict

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_yaml(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_registry(registry: dict) -> List[Dict]:
    issues = []
    providers = registry.get("providers") or {}
    if not providers:
        issues.append({"severity": "error", "message": "registry.providers missing or empty"})
        return issues
    for name, cfg in providers.items():
        if not cfg.get("model"):
            issues.append({"severity": "error", "message": f"provider '{name}' missing model"})
        caps = cfg.get("capabilities") or []
        if not isinstance(caps, list):
            issues.append({"severity": "error", "message": f"provider '{name}' capabilities must be a list"})
    return issues


def _validate_policies(policies: dict, path: str) -> List[Dict]:
    issues = []
    if policies is None:
        return issues
    if "max_latency_ms" in policies:
        v = policies.get("max_latency_ms")
        if not isinstance(v, (int, float)) or v < 0:
            issues.append({"severity": "error", "message": f"{path}.max_latency_ms must be non-negative number"})
    if "max_latency_ms_total" in policies:
        v = policies.get("max_latency_ms_total")
        if not isinstance(v, (int, float)) or v < 0:
            issues.append({"severity": "error", "message": f"{path}.max_latency_ms_total must be non-negative number"})
    if "on_sla_timeout" in policies:
        v = policies.get("on_sla_timeout")
        if v not in {"degrade", "abort"}:
            issues.append({"severity": "error", "message": f"{path}.on_sla_timeout must be one of ['degrade','abort']"})
    if "max_cost_usd_per_request" in policies:
        v = policies.get("max_cost_usd_per_request")
        if not isinstance(v, (int, float)) or v < 0:
            issues.append({"severity": "error", "message": f"{path}.max_cost_usd_per_request must be non-negative number"})
    if "required_capabilities" in policies:
        caps = policies.get("required_capabilities")
        if not isinstance(caps, list) or not all(isinstance(c, str) for c in caps):
            issues.append({"severity": "error", "message": f"{path}.required_capabilities must be list[str]"})
    return issues


def validate_routing(routing: dict, registry: dict) -> List[Dict]:
    issues = []
    providers = set((registry.get("providers") or {}).keys())
    # strategy type and weights
    strategy = (routing.get("strategy") or {})
    stype = strategy.get("type")
    if stype is not None and stype not in {"weighted"}:
        issues.append({"severity": "warning", "message": f"strategy.type '{stype}' is not recognized; supported: ['weighted']"})
    weights = (strategy.get("weights")) or {}
    for p in weights.keys():
        if p not in providers:
            issues.append({"severity": "error", "message": f"strategy.weights references unknown provider '{p}'"})
    # weight value checks
    if weights:
        bad = {k: v for k, v in weights.items() if not isinstance(v, (int, float))}
        if bad:
            issues.append({"severity": "error", "message": f"strategy.weights must be numbers, bad entries: {list(bad.keys())}"})
        neg = {k: v for k, v in weights.items() if isinstance(v, (int, float)) and v < 0}
        if neg:
            issues.append({"severity": "error", "message": f"strategy.weights must be non-negative, bad entries: {list(neg.keys())}"})
        total = sum(v for v in weights.values() if isinstance(v, (int, float)))
        # normalization hint (not enforced)
        if total > 0 and not (0.99 <= total <= 1.01):
            issues.append({"severity": "warning", "message": f"strategy.weights sum is {total:.4f}; consider normalizing to 1.0"})
    # global fallback_chain
    global_fc = routing.get("fallback_chain") or []
    for p in global_fc:
        if p not in providers:
            issues.append({"severity": "error", "message": f"fallback_chain includes unknown provider '{p}'"})
    # global policies
    issues.extend(_validate_policies(routing.get("policies") or {}, "policies"))
    # task_routing
    tr = routing.get("task_routing") or {}
    by_tool = tr.get("by_tool") or {}
    tool_fc = (tr.get("fallback_chain") or {})
    tool_policies = tr.get("policies") or {}
    for tool, provs in by_tool.items():
        if not isinstance(provs, list) or not provs:
            issues.append({"severity": "error", "message": f"task_routing.by_tool.{tool} must be a non-empty list"})
            continue
        unknown = [p for p in provs if p not in providers]
        if unknown:
            issues.append({"severity": "error", "message": f"task_routing.by_tool.{tool} includes unknown providers {unknown}"})
    for tool, provs in tool_fc.items():
        if not isinstance(provs, list) or not provs:
            issues.append({"severity": "error", "message": f"task_routing.fallback_chain.{tool} must be a non-empty list"})
            continue
        unknown = [p for p in provs if p not in providers]
        if unknown:
            issues.append({"severity": "error", "message": f"task_routing.fallback_chain.{tool} includes unknown providers {unknown}"})
    # precedence note when both by_tool and tool-level fallback exist
    both = sorted(set(by_tool.keys()) & set(tool_fc.keys()))
    for tool in both:
        issues.append({"severity": "warning", "message": f"tool '{tool}' has both by_tool and tool-level fallback_chain; by_tool takes precedence"})
    # tool policies shape
    for tool, pol in tool_policies.items():
        issues.extend(_validate_policies(pol, f"task_routing.policies.{tool}"))
        req_caps = (pol or {}).get("required_capabilities") or []
        if req_caps:
            # ensure at least one candidate in by_tool or tool_fc satisfies capabilities
            candidates = list(by_tool.get(tool) or []) + list(tool_fc.get(tool) or [])
            caps_map = {name: (registry.get("providers") or {}).get(name, {}).get("capabilities") or [] for name in candidates}
            satisfy = [name for name, caps in caps_map.items() if all(c in caps for c in req_caps)]
            if not satisfy:
                issues.append({"severity": "error", "message": f"task_routing.policies.{tool}.required_capabilities={req_caps} has no satisfying providers among candidates {candidates}"})

    # optional: tool schema awareness
    tools_dir = ROOT / "config" / "tools" / "schema"
    try:
        known_tools = []
        if tools_dir.exists() and tools_dir.is_dir():
            for p in tools_dir.iterdir():
                if p.is_file() and p.suffix.lower() in {".json", ".yaml", ".yml"}:
                    name = p.stem
                    known_tools.append(name)
        # warn if a tool schema exists but no routing is configured
        for t in known_tools:
            if t not in by_tool and t not in tool_fc and t not in tool_policies:
                issues.append({"severity": "warning", "message": f"tool '{t}' has schema but no routing (by_tool/fallback_chain/policies) configured"})
        # warn if routing references a tool but schema file is missing
        for t in sorted(set(list(by_tool.keys()) + list(tool_fc.keys()) + list(tool_policies.keys()))):
            if tools_dir.exists() and t not in known_tools:
                issues.append({"severity": "warning", "message": f"routing references tool '{t}' without a schema file"})
    except Exception:
        # be permissive; schema directory may not exist in tests
        pass

    # global coverage check: ensure at least one non-tool provider path exists
    has_default = registry.get("default_provider") in providers if registry.get("default_provider") else False
    has_global_fc = bool(routing.get("fallback_chain"))
    has_weights = bool(weights)
    if not (has_default or has_global_fc or has_weights):
        issues.append({"severity": "warning", "message": "no global provider resolution configured (default_provider, fallback_chain, or strategy.weights)"})
    return issues


def validate_all() -> Tuple[bool, List[Dict]]:
    registry = load_yaml(ROOT / "config" / "models" / "registry.yaml")
    routing = load_yaml(ROOT / "config" / "routing.yaml")
    issues = []
    issues.extend(validate_registry(registry))
    issues.extend(validate_routing(routing, registry))
    ok = not any(i.get("severity") == "error" for i in issues)
    return ok, issues


def main():
    ok, issues = validate_all()
    print(json.dumps({"ok": ok, "issues": issues}, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
