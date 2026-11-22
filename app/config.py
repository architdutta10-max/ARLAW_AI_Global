import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("ARLAW_DATA_DIR", ROOT / "data"))
DB_PATH = Path(os.getenv("ARLAW_DB_PATH", DATA_DIR / "arlaw.db"))
UPLOAD_DIR = Path(os.getenv("ARLAW_UPLOAD_DIR", DATA_DIR / "uploads"))
STATIC_DIR = Path(__file__).resolve().parent / "static"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")
TOP_K = int(os.getenv("ARLAW_TOP_K", "5"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
