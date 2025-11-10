from __future__ import annotations
from typing import List, Dict, Any, Tuple
import math
from .utils import read_events

def _percentile(values: List[float], p: float) -> float:
    if not values: return 0.0
    values = sorted(values)
    k = (len(values)-1) * (p/100.0)
    f = math.floor(k); c = math.ceil(k)
    if f == c: return float(values[int(k)])
    d0 = values[int(f)] * (c-k)
    d1 = values[int(c)] * (k-f)
    return float(d0+d1)

def summarize() -> Dict[str, Any]:
    evts = read_events()
    asks = [e for e in evts if e.get("type")=="ask"]
    fbs  = [e for e in evts if e.get("type")=="feedback"]

    lat = [e.get("latency_ms",0) for e in asks if isinstance(e.get("latency_ms"), (int,float))]
    llm = [e.get("llm_ms",0) for e in asks if isinstance(e.get("llm_ms"), (int,float))]
    ret = [e.get("retrieval_ms",0) for e in asks if isinstance(e.get("retrieval_ms"), (int,float))]

    # helpful rate joins by answer_id
    helpful_map = {e.get("answer_id"): e for e in fbs}
    helpful_marks = []
    for a in asks:
        fb = helpful_map.get(a.get("answer_id"))
        if fb is not None and isinstance(fb.get("helpful"), bool):
            helpful_marks.append(1 if fb["helpful"] else 0)

    by_model = {}
    for a in asks:
        m = a.get("model") or "unknown"
        by_model.setdefault(m, {"n":0,"lat":[]})
        by_model[m]["n"] += 1
        if isinstance(a.get("latency_ms"), (int,float)):
            by_model[m]["lat"].append(a["latency_ms"])

    return {
        "volume": len(asks),
        "latency_ms": {
            "p50": _percentile(lat, 50),
            "p95": _percentile(lat, 95),
        },
        "retrieval_ms": {
            "p50": _percentile(ret, 50),
            "p95": _percentile(ret, 95),
        },
        "llm_ms": {
            "p50": _percentile(llm, 50),
            "p95": _percentile(llm, 95),
        },
        "helpful_rate": (sum(helpful_marks)/len(helpful_marks)) if helpful_marks else None,
        "by_model": {
            m: {"n": d["n"], "latency_p50": _percentile(d["lat"], 50), "latency_p95": _percentile(d["lat"], 95)}
            for m, d in by_model.items()
        }
    }
