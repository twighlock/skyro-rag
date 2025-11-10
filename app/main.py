from __future__ import annotations

import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .metrics import summarize

from .debug_index import snapshot
import time, uuid
from .utils import log_event
from typing import Optional

from .state import STATE

from dotenv import load_dotenv
from .env import load as load_env  # if you added env loader earlier
load_env()

from .ingest.index import ingest_paths
from .retriever.hybrid import get_hybrid_retriever
from .rag import rag_ask
from .rag import answer_with_llm

app = FastAPI(title="Skyro RAG Demo", version="0.1.0")

# Optional CORS (won't hurt; useful if you ever open index.html directly from disk)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keep BM25 ref after /ingest
_STATE: Dict[str, Any] = {"bm25": None}

class IngestRequest(BaseModel):
    paths: List[str]

class AskRequest(BaseModel):
    question: str
    user_id: Optional[str] = None
    team: Optional[str] = None
    model: Optional[str] = None 

class FeedbackRequest(BaseModel):
    answer_id: str
    helpful: bool
    comment: Optional[str] = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/ingest")
def ingest(req: IngestRequest):
    res = ingest_paths(req.paths)
    STATE["bm25"] = res.get("bm25")
    return {"status": "ok", "indexed": res["indexed"], "chunks": res["chunks"]}

@app.post("/ask")
def ask(req: AskRequest):
    retriever = get_hybrid_retriever(bm25=_STATE.get("bm25"))

    t0 = time.perf_counter()
    docs = retriever.get_relevant_documents(req.question)
    t_retrieval = int((time.perf_counter() - t0) * 1000)

    if not docs:
        resp = {
            "answer": "I don’t have enough relevant context to answer. Please refine or add docs.",
            "citations": "",
            "model": req.model or os.getenv("CHAT_MODEL", "gpt-4o-mini"),
            "latency_ms": t_retrieval,
            "answer_id": str(uuid.uuid4()),
        }
        log_event({
            "type":"ask",
            "answer_id": resp["answer_id"],
            "q": req.question,
            "model": resp["model"],
            "retrieval_ms": t_retrieval,
            "llm_ms": 0,
            "latency_ms": t_retrieval,
            "retrieved": [],
            "citations": "",
            "tokens": None,
            "no_docs": True,
        })
        return resp

    t1 = time.perf_counter()
    out = answer_with_llm(req.question, docs, model=req.model)
    t_llm = int((time.perf_counter() - t1) * 1000)
    latency_ms = t_retrieval + t_llm

    answer_id = str(uuid.uuid4())
    out["answer_id"] = answer_id
    out["latency_ms"] = latency_ms

    usage = out.get("usage") if isinstance(out, dict) else None

    log_event({
        "type":"ask",
        "answer_id": answer_id,
        "q": req.question,
        "model": out.get("model"),
        "retrieval_ms": t_retrieval,
        "llm_ms": t_llm,
        "latency_ms": latency_ms,
        "retrieved": [d.metadata.get("source") for d in docs],
        "citations": out.get("citations",""),
        "tokens": usage,
    })
    return out

@app.get("/metrics")
def metrics():
    return summarize()


@app.get("/debug/index")
def debug_index(limit: int = 200):
    return snapshot(limit=limit)

@app.get("/eval")
def eval_endpoint(k: int = 8):
    from .eval_runner import run_eval 
    return run_eval(k=k, path="eval/questions.jsonl")
    
@app.post("/feedback")
def feedback(req: FeedbackRequest):
    log_event({
        "type":"feedback",
        "answer_id": req.answer_id,
        "helpful": req.helpful,
        "comment": req.comment,
    })
    return {"ok": True}

app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

@app.get("/")
def root():
    return {"open": "http://localhost:8000/ui/"}
