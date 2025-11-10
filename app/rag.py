from __future__ import annotations

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever

from .env import load as load_env
load_env()


DB_DIR = os.getenv("RAG_DB_DIR", ".chroma")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

def make_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=EMBED_MODEL)

def chunk_docs(docs: List[Document]) -> List[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, chunk_overlap=150, length_function=len, is_separator_regex=False
    )
    return splitter.split_documents(docs)

def build_or_load_vectorstore(chunks: List[Document]) -> Chroma:
    vs = Chroma(
        collection_name="skyro_rag",
        embedding_function=make_embeddings(),
        persist_directory=DB_DIR,  # using a persistent client under the hood
    )
    if chunks:
        vs.add_documents(chunks)
        try:
            vs.persist()  
        except AttributeError:
            pass
    return vs


def bm25_from_docs(docs: List[Document]) -> BM25Retriever:
    return BM25Retriever.from_documents(docs, k=8)

class SimpleHybridRetriever:
    """Version-agnostic hybrid retriever: interleave BM25 + dense."""
    def __init__(self, vs, bm25=None, top_k: int = 8):
        self.vs = vs
        self.bm25 = bm25
        self.top_k = top_k

    def _dense_docs(self, query: str):
        return self.vs.similarity_search(query, k=self.top_k) or []

    def _bm25_docs(self, query: str):
        if not self.bm25:
            return []
        # LC<=0.1: get_relevant_documents ; LC>=0.2: invoke
        try:
            return self.bm25.get_relevant_documents(query)
        except AttributeError:
            return self.bm25.invoke(query)

    def get_relevant_documents(self, query: str):
        dense_docs = self._dense_docs(query)
        bm25_docs = self._bm25_docs(query)

        seen = set()
        def _key(d):
            return (
                d.metadata.get("source"),
                d.metadata.get("page"),
                d.metadata.get("section"),
                hash(d.page_content[:200]),
            )

        combined = []
        i = 0
        while (i < max(len(dense_docs), len(bm25_docs))) and len(combined) < self.top_k:
            if i < len(bm25_docs):
                k = _key(bm25_docs[i])
                if k not in seen:
                    seen.add(k); combined.append(bm25_docs[i])
            if i < len(dense_docs) and len(combined) < self.top_k:
                k = _key(dense_docs[i])
                if k not in seen:
                    seen.add(k); combined.append(dense_docs[i])
            i += 1

        for d in dense_docs + bm25_docs:
            if len(combined) >= self.top_k: break
            k = _key(d)
            if k not in seen:
                seen.add(k); combined.append(d)
        return combined


def make_retriever(vs: Chroma, bm25: Optional[BM25Retriever] = None):
    # No .as_retriever(); we use vs.similarity_search inside SimpleHybridRetriever
    return SimpleHybridRetriever(vs=vs, bm25=bm25, top_k=8)


def format_citations(docs: List[Document]) -> str:
    lines = []
    seen = set()
    for i, d in enumerate(docs[:5], start=1):
        src = d.metadata.get("source", "unknown")
        sect = d.metadata.get("section") or d.metadata.get("title") or ""
        key = (src, sect)
        if key in seen:
            continue
        seen.add(key)
        preview = d.page_content.strip().replace("\n", " ")
        if len(preview) > 280:
            preview = preview[:280] + "..."
        lines.append(f"[{i}] {src} {f'— {sect}' if sect else ''}\n    “{preview}”")
    return "\n".join(lines)

SYSTEM_PROMPT = (
    "You are an enterprise documentation assistant. "
    "Always respond in **English**, even if the question is in another language. "
    "Answer concisely and only based on the provided context snippets. "
    "If the answer is not present in the context, clearly say you don't know."
)

# --- in app/rag.py ---

# --- paste into app/rag.py (replace existing versions) ---

ALLOWED_MODELS = {"gpt-5","gpt-5-mini","gpt-5-nano","gpt-4o","gpt-4o-mini"}

def _normalize_model(name: str | None) -> str | None:
    if not name:
        return None
    return name if name in ALLOWED_MODELS else None

def answer_with_llm(question: str, docs: list[Document], model: str | None = None) -> dict:
    chat_model = _normalize_model(model) or os.getenv("CHAT_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=chat_model, temperature=0.2)

    context_blocks = []
    for i, d in enumerate(docs[:5], start=1):
        context_blocks.append(f"[{i}] SOURCE={d.metadata.get('source','unknown')}\n{d.page_content}")
    context = "\n\n".join(context_blocks)

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"# Question:\n{question}\n\n"
        f"# Context (snippets):\n{context}\n\n"
        f"# Instructions:\n"
        f"- Provide a concise answer (3–6 sentences).\n"
        f"- Cite snippets as [1], [2], etc.\n"
        f"- Do not invent facts outside the context.\n"
    )
    resp = llm.invoke(prompt)
    return {"answer": resp.content, "citations": format_citations(docs), "model": chat_model}

def rag_ask(question: str, retriever, model: str | None = None, **_ignored) -> dict:
    model = _normalize_model(model)
    retrieved = retriever.get_relevant_documents(question)
    if not retrieved:
        return {
            "answer": "I couldn't find an answer in the indexed documents. Please refine your question or add documents.",
            "citations": "",
            "model": model or os.getenv("CHAT_MODEL", "gpt-4o-mini"),
        }
    return answer_with_llm(question, retrieved, model=model)

# --- end patch ---



def rag_ask(question: str, retriever) -> Dict[str, Any]:
    retrieved = retriever.get_relevant_documents(question)
    if not retrieved:
        return {
            "answer": "I couldn't find an answer in the indexed documents. Please refine your question or add documents.",
            "citations": "",
        }
    return answer_with_llm(question, retrieved)
