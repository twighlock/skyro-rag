from __future__ import annotations
import os, json, time, threading
from pathlib import Path
from typing import Dict, Any, Iterable, List

_LOG_PATH = Path(".logs/events.jsonl")
_LOCK = threading.Lock()

def log_event(evt: Dict[str, Any], path: Path = _LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    evt = dict(evt)
    evt["ts"] = time.time()
    line = json.dumps(evt, ensure_ascii=False)
    with _LOCK:
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

def read_events(path: Path = _LOG_PATH) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]
