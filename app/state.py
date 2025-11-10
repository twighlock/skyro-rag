from __future__ import annotations

# Single shared state dict for the app
STATE = {
    "bm25": None,          # set after /ingest
    "collection_name": "skyro_rag",
    "persist_dir": ".chroma",
}