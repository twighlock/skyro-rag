from __future__ import annotations
from typing import List
from langchain_core.documents import Document 
from .loaders import load_path
from ..rag import chunk_docs, build_or_load_vectorstore, bm25_from_docs

def ingest_paths(paths: List[str]):
    # 1) загрузка
    raw_docs: List[Document] = []
    for p in paths:
        raw_docs += load_path(p)

    if not raw_docs:
        return {"indexed": 0, "chunks": 0}

    # 2) чанкинг
    chunks = chunk_docs(raw_docs)

    # 3) upsert в векторку
    vs = build_or_load_vectorstore(chunks)

    # 4) BM25 для гибридного поиска
    bm25 = bm25_from_docs(chunks)
    return {"indexed": len(raw_docs), "chunks": len(chunks), "bm25": bm25}
