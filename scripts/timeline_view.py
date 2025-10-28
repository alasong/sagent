import argparse
import json
from pathlib import Path
from typing import List, Dict, Optional


ROOT = Path(__file__).resolve().parents[1]


def load_session_events(session_id: str, root: Optional[Path] = None) -> List[Dict]:
    base = (root or ROOT) / "logs" / "sessions" / f"{session_id}.jsonl"
    if not base.exists():
        return []
    events = []
    with open(base, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                # 跳过非JSON行
                continue
    return events


def filter_events(events: List[Dict], event: Optional[str] = None, provider: Optional[str] = None) -> List[Dict]:
    out = []
    for e in events:
        if event and e.get("event") != event:
            continue
        if provider:
            details = e.get("details") or {}
            if details.get("provider") != provider:
                continue
        out.append(e)
    return out


def summarize_events(events: List[Dict]) -> Dict:
    summary = {
        "total_events": len(events),
        "by_event": {},
        "latency_ms": {
            "count": 0,
            "avg": None,
            "p50": None,
            "p95": None,
        },
        "provider_success_rate": None,
    }
    # 事件计数
    from collections import Counter
    counter = Counter([e.get("event") for e in events])
    summary["by_event"] = dict(counter)
    # 成功率
    succ = counter.get("provider_success", 0)
    fail = counter.get("provider_failed", 0)
    total_pf = succ + fail
    if total_pf > 0:
        summary["provider_success_rate"] = round(succ / total_pf, 4)
    # 延迟统计：从details.duration_ms采样
    latencies = []
    for e in events:
        d = e.get("details") or {}
        v = d.get("duration_ms")
        if isinstance(v, (int, float)):
            latencies.append(float(v))
    if latencies:
        latencies.sort()
        count = len(latencies)
        avg = sum(latencies) / count
        def pct(p: float):
            if count == 0:
                return None
            idx = int(max(0, min(count - 1, round(p * (count - 1)))))
            return latencies[idx]
        summary["latency_ms"] = {
            "count": count,
            "avg": round(avg, 2),
            "p50": round(pct(0.5), 2),
            "p95": round(pct(0.95), 2),
        }
    return summary


def main():
    parser = argparse.ArgumentParser(description="View session timeline JSONL")
    parser.add_argument("--session", required=True, help="session_id to view")
    parser.add_argument("--event", help="filter by event name")
    parser.add_argument("--provider", help="filter by provider name")
    parser.add_argument("--summary", action="store_true", help="show summary instead of raw events")
    args = parser.parse_args()

    events = load_session_events(args.session)
    if not events:
        print(json.dumps({"error": "no events", "session_id": args.session}, ensure_ascii=False))
        return
    events = filter_events(events, event=args.event, provider=args.provider)
    if args.summary:
        print(json.dumps(summarize_events(events), ensure_ascii=False, indent=2))
    else:
        for e in events:
            print(json.dumps(e, ensure_ascii=False))


if __name__ == "__main__":
    main()

