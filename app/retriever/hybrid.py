from __future__ import annotations
from langchain_chroma import Chroma
from ..rag import make_retriever, make_embeddings  # <-- add make_embeddings

def get_hybrid_retriever(bm25=None):
    vs = Chroma(
        collection_name="skyro_rag",
        persist_directory=".chroma",
        embedding_function=make_embeddings(),   # <-- important
    )
    return make_retriever(vs, bm25=bm25)
