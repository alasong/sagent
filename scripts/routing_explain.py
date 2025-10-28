import argparse
import json
from pathlib import Path
from typing import Dict, Any, List

from scripts import poc_local_validate as poc


def _load_session_events(session_id: str) -> List[Dict[str, Any]]:
    logs_dir = poc.ROOT / "logs" / "sessions"
    path = logs_dir / f"{session_id}.jsonl"
    events: List[Dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    return events


def _summarize_session(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    states: Dict[str, Dict[str, Any]] = {}
    attempts: Dict[str, int] = {}
    successes: Dict[str, int] = {}
    failures: Dict[str, int] = {}
    for ev in events:
        d = ev.get("details") or {}
        p = d.get("provider")
        name = ev.get("event")
        if not p:
            continue
        if name == "circuit_open":
            states[p] = {"state": "open", "reason": d.get("reason")}
        elif name == "circuit_half_open":
            states[p] = {"state": "half_open"}
        elif name == "circuit_closed":
            states[p] = {"state": "closed"}
        elif name == "circuit_skip_open":
            states[p] = {"state": "open", "skipped": True}
        elif name == "provider_attempt":
            attempts[p] = attempts.get(p, 0) + 1
        elif name == "provider_success":
            successes[p] = successes.get(p, 0) + 1
        elif name == "provider_failed":
            failures[p] = failures.get(p, 0) + 1
    return {"states": states, "attempts": attempts, "successes": successes, "failures": failures}


def explain_routing(tool: str | None = None, session_id: str | None = None) -> Dict[str, Any]:
    registry = poc.load_yaml(poc.ROOT / "config" / "models" / "registry.yaml")
    routing = poc.load_routing_config()
    providers = registry.get("providers", {})
    ordered = poc.select_providers_for_tool(registry, routing, tool)
    # 计算生效策略
    tool_policies = ((routing.get("task_routing", {}) or {}).get("policies", {}) or {}).get(tool) or {}
    global_policies = routing.get("policies", {}) or {}
    effective_policies = {**global_policies, **tool_policies}
    # 每个提供方的策略允许性（成本/能力）
    details = []
    for name in ordered:
        cfg = providers.get(name) or {}
        allowed = poc.policy_allows_provider(cfg, effective_policies, est_tokens=1000)
        details.append({"provider": name, "model": cfg.get("model"), "allowed_by_policy": allowed})
    # 会话状态（可选）
    session_summary = None
    if session_id:
        session_summary = _summarize_session(_load_session_events(session_id))
    # 策略来源说明
    source = {
        "by_tool": ((routing.get("task_routing", {}) or {}).get("by_tool", {}) or {}).get(tool),
        "tool_fallback_chain": ((routing.get("task_routing", {}) or {}).get("fallback_chain", {}) or {}).get(tool),
        "global_fallback_chain": routing.get("fallback_chain"),
        "strategy": routing.get("strategy"),
    }
    return {
        "tool": tool,
        "ordered": ordered,
        "policies": effective_policies,
        "providers": details,
        "source": source,
        "session": session_summary,
    }


def main():
    ap = argparse.ArgumentParser(description="Explain routing decisions for a tool and optional session context")
    ap.add_argument("--tool", dest="tool", default=None, help="Tool name, e.g., calc/search")
    ap.add_argument("--session", dest="session", default=None, help="Session id to include runtime circuit state and attempts")
    ap.add_argument("--json", dest="json_out", action="store_true", help="Output JSON instead of text")
    args = ap.parse_args()
    info = explain_routing(args.tool, args.session)
    if args.json_out:
        print(json.dumps(info, ensure_ascii=False))
        return
    print(f"Tool: {info['tool']}")
    print("Ordered providers:")
    for i, p in enumerate(info["ordered"], 1):
        item = next((d for d in info["providers"] if d["provider"] == p), {"allowed_by_policy": True})
        allowed = "allowed" if item.get("allowed_by_policy") else "blocked_by_policy"
        print(f"  {i}. {p} ({allowed})")
    print("Policies:")
    print(json.dumps(info["policies"], ensure_ascii=False, indent=2))
    if info.get("session"):
        print("Session state:")
        print(json.dumps(info["session"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

