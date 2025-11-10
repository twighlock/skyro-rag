from __future__ import annotations
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

def load():
    path = find_dotenv(filename=".env", usecwd=True)
    if not path:
        path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=path, override=False)

