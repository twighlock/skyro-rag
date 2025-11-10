from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
import json, math

from langchain_chroma import Chroma
from langchain_core.documents import Document

from .state import STATE
from .rag import make_embeddings  
import os

_EQUIV_EXT = {"csv","yaml","yml","txt","md"}

def _norm_source(s: str) -> str:
    return s.replace("\\", "/")

def _name_key(p: str) -> str:
    p = _norm_source(p)
    base = os.path.basename(p).lower()
    name, ext = os.path.splitext(base)
    ext = ext.lstrip(".")
    bucket = "txt" if ext in _EQUIV_EXT else ext
    return f"{name}.{bucket}"

def _gold_hit(top_sources, gold_paths) -> bool:
    top_keys  = {_name_key(s) for s in top_sources}
    gold_keys = {_name_key(g) for g in gold_paths}
    return not top_keys.isdisjoint(gold_keys)


class LocalHybridRetriever:
    def __init__(self, vs: Chroma, bm25=None, top_k: int = 8):
        self.vs = vs
        self.bm25 = bm25
        self.top_k = top_k
        # If the BM25 retriever supports a .k attribute, set it
        try:
            if hasattr(self.bm25, "k"):
                self.bm25.k = top_k
        except Exception:
            pass

    def _bm25_docs(self, query: str):
        if not self.bm25:
            return []
        try:
            # Newer API (Runnable)
            if hasattr(self.bm25, "invoke"):
                res = self.bm25.invoke(query)
            # Older API
            elif hasattr(self.bm25, "get_relevant_documents"):
                res = self.bm25.get_relevant_documents(query)
            else:
                res = []
        except Exception:
            res = []
        # Ensure list and truncate
        if not isinstance(res, list):
            res = list(res) if res is not None else []
        return res[: self.top_k]

    def get_relevant_documents(self, query: str) -> List[Document]:
        # Dense
        try:
            dense_docs = self.vs.similarity_search(query, k=self.top_k) or []
        except Exception:
            dense_docs = []
        # Sparse (BM25)
        bm25_docs = self._bm25_docs(query)

        # Simple fusion + dedup
        seen, out = set(), []
        for d in dense_docs + bm25_docs:
            key = (d.metadata.get("source"), d.page_content[:160])
            if key in seen:
                continue
            seen.add(key)
            out.append(d)
        return out[: self.top_k]

def _dcg(rel):
    import math
    return sum(r / math.log2(i + 2) for i, r in enumerate(rel))

def _rel_vector(sources, gold, k=8):
    # 1 if this individual source matches any gold (using filename-based equivalence)
    return [1 if _gold_hit([s], gold) else 0 for s in sources[:k]]

def _ndcg_at_k(sources, gold, k=8):
    rel = _rel_vector(sources, gold, k)
    idcg = _dcg(sorted(rel, reverse=True))
    return 0.0 if idcg == 0 else _dcg(rel) / idcg

def _build_retriever(top_k: int = 8) -> LocalHybridRetriever:
    vs = Chroma(
        collection_name=STATE.get("collection_name", "skyro_rag"),
        persist_directory=STATE.get("persist_dir", ".chroma"),
        embedding_function=make_embeddings(),
    )
    return LocalHybridRetriever(vs=vs, bm25=STATE.get("bm25"), top_k=top_k)

def run_eval(k: int = 8, path: str = "eval/questions.jsonl") -> Dict[str, Any]:
    retriever = _build_retriever(top_k=k)
    items = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    n = len(items)
    hits = grounded_hits = 0
    ndcgs: List[float] = []
    for it in items:
        q, gold, must = it["q"], it["gold"], it.get("must_contain", [])
        docs = retriever.get_relevant_documents(q)
        sources = [d.metadata.get("source","") for d in docs]
        if _gold_hit(sources[:k], gold):
            hits += 1
        ndcgs.append(_ndcg_at_k(sources, gold, k=k))

        context = " ".join(d.page_content for d in docs[:k])[:20000].lower()
        grounded = (_gold_hit(sources[:k], gold) and all(m.lower() in context for m in must))

        grounded_hits += 1 if grounded else 0
    return {
        f"n": n,
        f"recall@{k}": hits / n if n else 0.0,
        f"mean_nDCG@{k}": (sum(ndcgs) / n) if n else 0.0,
        f"groundedness@{k}": grounded_hits / n if n else 0.0,
    }
