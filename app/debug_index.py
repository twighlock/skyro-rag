from __future__ import annotations
from typing import Any, Dict, List
from collections import Counter
import os

from langchain_chroma import Chroma
from .state import STATE
from .rag import make_embeddings

def snapshot(limit: int = 200) -> Dict[str, Any]:
    vs = Chroma(
        collection_name=STATE.get("collection_name","skyro_rag"),
        persist_directory=STATE.get("persist_dir",".chroma"),
        embedding_function=make_embeddings(),
    )

    # Try modern chromadb get() signature
    try:
        got = vs._collection.get(include=["metadatas","documents"], limit=limit)
        ids = got.get("ids", [])  # ids are returned even if not requested in include
        metadatas = got.get("metadatas", []) or []
        documents = got.get("documents", []) or []
        n = min(len(ids), len(metadatas), len(documents))
        items = []
        for i in range(n):
            md = metadatas[i] or {}
            src = md.get("source") or md.get("filename") or ""
            items.append({
                "id": ids[i],
                "source": src,
                "filename": os.path.basename(str(src)) if src else "",
            })
    except Exception as e:
        # Fallback: derive a snapshot via a sample search
        try:
            docs = vs.similarity_search("status payout provider risk limits oncall postmortem", k=min(50, limit))
            items = [{
                "id": f"sample_{i}",
                "source": (d.metadata or {}).get("source",""),
                "filename": os.path.basename((d.metadata or {}).get("source","")) if (d.metadata or {}).get("source") else ""
            } for i, d in enumerate(docs)]
        except Exception as e2:
            return {"error": f"cannot inspect collection: {e}; fallback failed: {e2}"}

    by_file = Counter(x["filename"].lower() for x in items if x["filename"])
    unique_sources = sorted({x["source"] for x in items if x["source"]})

    return {
        "count_sampled": len(items),
        "unique_filenames": len(by_file),
        "top_filenames": by_file.most_common(20),
        "sample_sources": unique_sources[:20],
    }
