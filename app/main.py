from __future__ import annotations

import hashlib
import io
import json
import os
import re
import threading
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from .config import STATIC_DIR, UPLOAD_DIR, TOP_K
from .knowledge import init_db, add_source, search, list_sources, seed_builtin_knowledge
from .llm import generate, provider_order, classify_task

VERSION = "3.0.0"
MAX_UPLOAD_BYTES = int(os.getenv("ARLAW_MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
MAX_PDF_PAGES = int(os.getenv("ARLAW_MAX_PDF_PAGES", "300"))
CHAT_RATE_LIMIT = int(os.getenv("ARLAW_CHAT_RATE_LIMIT", "20"))
UPLOAD_RATE_LIMIT = int(os.getenv("ARLAW_UPLOAD_RATE_LIMIT", "5"))
RATE_WINDOW_SECONDS = 60

# Process-local protection. For multi-worker/multi-instance production deployments,
# put rate limiting at the reverse proxy or use a shared Redis-backed limiter.
_rate_lock = threading.Lock()
_rate_events: dict[tuple[str, str], deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    # Do not trust X-Forwarded-For from arbitrary clients. Render terminates TLS
    # and supplies the ASGI client address; proxy-specific trust can be configured later.
    return request.client.host if request.client else "unknown"


def _rate_limit(request: Request, bucket: str, limit: int) -> None:
    now = time.monotonic()
    key = (_client_key(request), bucket)
    with _rate_lock:
        events = _rate_events[key]
        while events and now - events[0] >= RATE_WINDOW_SECONDS:
            events.popleft()
        if len(events) >= limit:
            retry = max(1, int(RATE_WINDOW_SECONDS - (now - events[0])))
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait before trying again.",
                headers={"Retry-After": str(retry)},
            )
        events.append(now)
        # Bound memory if many client addresses are seen.
        if len(_rate_events) > 10000:
            stale = [k for k, q in _rate_events.items() if not q or now - q[-1] >= RATE_WINDOW_SECONDS]
            for stale_key in stale:
                _rate_events.pop(stale_key, None)


def _jurisdiction_codes() -> set[str]:
    data = json.loads((Path(__file__).parent / "jurisdictions.json").read_text(encoding="utf-8"))
    return {
        str(item["code"]).upper()
        for group in data.get("groups", [])
        for item in group.get("items", [])
        if item.get("code")
    }


SUPPORTED_JURISDICTIONS = _jurisdiction_codes()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_builtin_knowledge()
    yield


app = FastAPI(
    title="ARLAW AI Global",
    version=VERSION,
    description="Jurisdiction-aware AI legal, civil and economic research assistance",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    response.headers.setdefault("Cache-Control", "no-store" if request.url.path.startswith("/api/") else "public, max-age=300")
    return response


@app.get("/")
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "product": "ARLAW AI Global",
        "version": VERSION,
        "mode": "local-and-cloud-hybrid",
        "disclaimer": "Research and workflow assistance only; not professional representation, certification or judicial decision-making.",
    }


@app.get("/api/capabilities")
def capabilities():
    return {
        "professional_workspaces": [
            {"id": "lawyer_assistance", "name": "Lawyer & Advocate Assistance", "scope": "Research, issue spotting, drafting support and matter organisation", "boundary": "Does not represent clients or certify court filings."},
            {"id": "accounting", "name": "Accounting Support", "scope": "Bookkeeping explanations, reconciliations and financial statement analysis", "boundary": "Does not certify accounts or conduct statutory audits."},
            {"id": "ca_tax", "name": "CA & Tax Support", "scope": "Tax research, worked calculations and compliance preparation", "boundary": "Does not sign, attest, certify or conduct regulated audits."},
            {"id": "judicial_research", "name": "Judicial Research Support", "scope": "Neutral issue, evidence and precedent organisation", "boundary": "Does not determine guilt, liability, credibility or case outcomes."},
            {"id": "legal_research", "name": "Legal Research", "scope": "Jurisdiction-aware legal information and source-grounded research", "boundary": "Not a substitute for qualified legal advice."},
        ],
        "supported_languages_prompted": ["English", "Hindi", "Bengali", "other languages when supported by the configured model"],
        "verification": "Citation labels are checked for reference existence and paragraph coverage only; source support, currency and legal correctness require human verification.",
        "security_note": "Use authentication, shared rate limiting, persistent storage and independent security review before accepting confidential or privileged records.",
    }


@app.get("/api/health/model")
def model_health():
    providers = provider_order()
    return {
        "providers": providers,
        "primary_provider": providers[0] if providers else None,
        "groq_configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "ollama_enabled": os.getenv("OLLAMA_ENABLED", "true").lower() in {"1", "true", "yes", "on"},
        "ollama_model": os.getenv("OLLAMA_MODEL", "qwen3:8b"),
        "local_models": True,
        "multi_model_review": False,
    }


@app.get("/api/jurisdictions")
def jurisdictions():
    return json.loads((Path(__file__).parent / "jurisdictions.json").read_text(encoding="utf-8"))


@app.get("/api/registry")
def source_registry():
    return json.loads((Path(__file__).parent / "sources_registry.json").read_text(encoding="utf-8"))


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=14000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    jurisdiction: str = Field(default="GLOBAL", min_length=1, max_length=80)
    use_knowledge: bool = True

    @field_validator("jurisdiction")
    @classmethod
    def validate_jurisdiction(cls, value: str) -> str:
        normalized = value.strip().upper()
        if normalized not in SUPPORTED_JURISDICTIONS:
            raise ValueError("Unsupported jurisdiction code. Select a code from /api/jurisdictions.")
        return normalized


@app.post("/api/chat")
def chat(req: ChatRequest, request: Request):
    _rate_limit(request, "chat", CHAT_RATE_LIMIT)
    messages = [m.model_dump() for m in req.messages]
    last = next((m for m in reversed(messages) if m.get("role") == "user"), None)
    if not last:
        raise HTTPException(400, "A user message is required.")
    question = last["content"]
    hits = search(question, TOP_K, req.jurisdiction, classify_task(question)) if req.use_knowledge else []
    context = []
    citations = []
    for i, hit in enumerate(hits, 1):
        label = f"S{i}"
        context.append(
            f"[{label}] {hit['title']} | Jurisdiction: {hit['jurisdiction']} | "
            f"Jurisdiction relationship: {hit.get('jurisdiction_relation', 'unspecified')} | "
            f"Declared authority: {hit['authority']} (ranking priority {hit.get('authority_priority', 0)}; not independently verified) | "
            f"Language: {hit['language']} | Recorded date: {hit['as_of'] or 'not supplied'} "
            f"(does not establish current validity) | URL: {hit['source_url'] or 'not supplied'}\n{hit['content']}"
        )
        citations.append({
            "label": label,
            "title": hit["title"],
            "jurisdiction": hit["jurisdiction"],
            "jurisdiction_relation": hit.get("jurisdiction_relation", "unspecified"),
            "authority": hit["authority"],
            "authority_priority": hit.get("authority_priority", 0),
            "language": hit["language"],
            "category": hit.get("category", "general"),
            "retrieval_relevance": hit.get("relevance"),
            "as_of": hit["as_of"],
            "url": hit["source_url"],
        })
    answer, error, model_info = generate(messages, "\n\n".join(context), [c["label"] for c in citations])
    if error:
        answer = "ARLAW could not connect to any configured AI provider.\n\n" + error
    return {
        "answer": answer,
        "citations": citations,
        "model_connected": error is None,
        "model": model_info,
        "jurisdiction": req.jurisdiction,
        "task": model_info.get("task"),
        "citation_validation": model_info.get("citation_validation"),
        "quality": model_info.get("quality"),
        "quality_warning": model_info.get("quality_warning"),
        "incomplete": model_info.get("incomplete", False),
    }


def _safe_upload_name(original_name: str, suffix: str) -> str:
    # Never persist the client-supplied path or potentially identifying filename.
    digest = hashlib.sha256(os.urandom(32)).hexdigest()[:20]
    return f"{digest}{suffix}"


@app.post("/api/documents")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form(""),
    jurisdiction: str = Form("GLOBAL"),
    source_url: str = Form(""),
    as_of: str = Form(""),
    authority: str = Form("unspecified"),
    language: str = Form("und"),
):
    _rate_limit(request, "upload", UPLOAD_RATE_LIMIT)
    original_name = Path(file.filename or "upload").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in {".txt", ".md", ".pdf"}:
        raise HTTPException(415, "Only .txt, .md and text-based .pdf are supported.")
    jurisdiction = jurisdiction.strip().upper()
    if jurisdiction not in SUPPORTED_JURISDICTIONS:
        raise HTTPException(422, "Unsupported jurisdiction code. Select a code from /api/jurisdictions.")
    if source_url.strip():
        parsed = urlparse(source_url.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise HTTPException(422, "Source URL must be an absolute HTTP or HTTPS URL.")
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    await file.close()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"Maximum upload size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    if not raw:
        raise HTTPException(400, "The uploaded file is empty.")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(raw), strict=True)
            if reader.is_encrypted:
                raise HTTPException(400, "Password-protected PDFs are not supported.")
            if len(reader.pages) > MAX_PDF_PAGES:
                raise HTTPException(413, f"PDFs are limited to {MAX_PDF_PAGES} pages.")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(400, "Could not safely extract text from this PDF.")
    else:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(400, "Text uploads must use UTF-8 encoding.")
    if len(text.strip()) < 40:
        raise HTTPException(400, "Too little extractable text. Scanned PDFs need OCR before upload.")
    if len(text) > 5_000_000:
        raise HTTPException(413, "Extracted document text exceeds the 5 MB indexing limit.")
    safe_name = _safe_upload_name(original_name, suffix)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / safe_name).write_bytes(raw)
    result = add_source(
        title.strip()[:240] or (Path(original_name).stem[:200] or "Uploaded document"),
        text,
        jurisdiction,
        source_url.strip(),
        as_of.strip()[:40],
        safe_name,
        authority.strip()[:40],
        language.strip()[:20],
    )
    return {"message": "Indexed locally", "file": safe_name, **result}


@app.get("/api/sources")
def sources():
    return {"sources": list_sources()}
