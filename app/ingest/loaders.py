from __future__ import annotations
import os, json
from typing import List
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_core.documents import Document

def load_path(path: str) -> List[Document]:
    path = path.strip()
    if os.path.isdir(path):
        docs: List[Document] = []
        for root, _, files in os.walk(path):
            for f in files:
                docs += load_file(os.path.join(root, f))
        return docs
    return load_file(path)

def load_file(path: str) -> List[Document]:
    ext = os.path.splitext(path)[1].lower()
    if ext in [".md", ".txt"]:
        loader = TextLoader(path, encoding="utf-8")
        docs = loader.load()
        for d in docs:
            d.metadata["source"] = os.path.relpath(path)
        return docs
    if ext == ".pdf":
        loader = PyPDFLoader(path)
        docs = loader.load()
        for d in docs:
            d.metadata["source"] = os.path.relpath(path)
        return docs
    if ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Превратим JSON в один документ с красивым текстом
        text = json.dumps(data, ensure_ascii=False, indent=2)
        return [Document(page_content=text, metadata={"source": os.path.relpath(path)})]
    # игнорим бинарные и прочее
    return []
