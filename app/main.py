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
from .llm import generate, provider_order, classify_task, fit_context
from .ambiguity import clarification_for, names_specific_authority

VERSION = "3.2.0"
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


# Explicit jurisdiction routing is applied only when the user selects GLOBAL.
# A deliberate country selection remains authoritative and is never silently overridden.
_JURISDICTION_MARKERS = (
    ("IN", re.compile(
        r"\b(?:india|indian|rbi|reserve bank of india|constitution of india|supreme court of india|"
        r"bharatiya nyaya sanhita|bharatiya nagarik suraksha sanhita|bharatiya sakshya adhiniyam|"
        r"digital personal data protection|dpdp act|indian contract act|limitation act,?\s*1963|"
        r"bns\s*,?\s*2023|bnss\s*,?\s*2023|bsa\s*,?\s*2023)\b", re.I
    )),
    ("DE", re.compile(r"\b(?:germany|german)\b", re.I)),
    ("UK", re.compile(r"\b(?:united kingdom|u\.?k\.?|british|england and wales|scotland|northern ireland)\b", re.I)),
    ("US", re.compile(r"\b(?:united states|u\.?s\.?a?\.?|american)\b", re.I)),
    ("EU", re.compile(r"\b(?:european union|e\.?u\.?|eu law|eu regulation|gdpr)\b", re.I)),
    ("SG", re.compile(r"\b(?:singapore|singaporean)\b", re.I)),
    ("CA", re.compile(r"\b(?:canada|canadian)\b", re.I)),
    ("AU", re.compile(r"\b(?:australia|australian)\b", re.I)),
    ("NZ", re.compile(r"\b(?:new zealand)\b", re.I)),
    ("BD", re.compile(r"\b(?:bangladesh|bangladeshi)\b", re.I)),
    ("PK", re.compile(r"\b(?:pakistan|pakistani)\b", re.I)),
    ("FR", re.compile(r"\b(?:france|french)\b", re.I)),
    ("IE", re.compile(r"\b(?:ireland|irish)\b", re.I)),
)
_INTERNATIONAL_MARKER = re.compile(
    r"\b(?:international law|international trade|international approach(?:es)?|"
    r"international framework(?:s)?|international standard(?:s)?|cross-border|cross border|"
    r"international sanctions|sanctions?|transnational)\b", re.I
)
_LEGAL_TOPIC_MARKER = re.compile(
    r"\b(?:law|laws|legal|court|case|statute|constitution|regulation|regulatory|"
    r"rights|contract|fraud|sanctions?|cartel|antitrust|competition|privacy|"
    r"data protection|jurisdiction|criminal|civil|burden of proof|rbi|compliance|liability|"
    r"international trade|trade law|trade compliance|export[- ]controls?|"
    r"import[- ]export|customs law|tariffs?|embargo(?:es)?)\b",
    re.I,
)
_QUESTION_HEADING = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?(?:QUESTION\s+)?"
    r"(\d{1,2})\s*(?:\\?[.)\u2014\u2013:?-])\s*"
    r"(.*?)(?:\*\*)?\s*$"
)


def _split_research_sections(question: str) -> list[dict]:
    """Split explicitly numbered QUESTION headings without splitting ordinary prose."""
    matches = list(_QUESTION_HEADING.finditer(question or ""))
    if len(matches) < 2:
        return [{"number": None, "title": "", "text": question or ""}]
    sections = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(question)
        body = (question[start:end] or "").strip()
        sections.append({
            "number": int(match.group(1)),
            "title": (match.group(2) or "").strip(),
            "text": body,
        })
    return sections


def _explicit_jurisdictions(text: str) -> list[str]:
    """Return only jurisdictions explicitly named in a question section."""
    found = [code for code, pattern in _JURISDICTION_MARKERS if pattern.search(text or "")]
    if _INTERNATIONAL_MARKER.search(text or "") and "INTL" in SUPPORTED_JURISDICTIONS:
        found.append("INTL")
    # Preserve marker order while removing duplicates and unsupported codes.
    return list(dict.fromkeys(code for code in found if code in SUPPORTED_JURISDICTIONS))


def _section_task(text: str) -> str:
    """Prevent economic keywords from masking an explicitly legal research task."""
    task = classify_task(text)
    if task in {"finance_tax", "accounting", "ca_tax", "general"} and _LEGAL_TOPIC_MARKER.search(text or ""):
        return "legal_research"
    return task


def _retrieve_request(question: str, selected_jurisdiction: str, top_k: int):
    """Retrieve per question and per explicit jurisdiction for GLOBAL/mixed prompts.

    Returns (hits, coverage, aggregate_task). If a specific jurisdiction is selected,
    it remains the sole jurisdiction searched. Missing sources are recorded per section.
    """
    sections = _split_research_sections(question)
    combined_hits = []
    seen_ids = set()
    coverage = []
    section_tasks = []

    for section in sections:
        # The heading often carries the jurisdiction/topic (e.g. "Privacy: Germany").
        # Keep it in the routing/search query rather than silently dropping it.
        body = section["text"] or question
        text = (section.get("title", "") + "\n" + body).strip()
        section_task = _section_task(text)
        section_tasks.append(section_task)
        if selected_jurisdiction != "GLOBAL":
            jurisdictions = [selected_jurisdiction]
        else:
            jurisdictions = _explicit_jurisdictions(text) or ["GLOBAL"]

        per_jurisdiction = []
        # Allocate source slots across jurisdictions before packing the context.
        # One country must not consume the entire context budget in a global query.
        requested_k = min(max(int(top_k), 1), 3)
        if len(jurisdictions) >= 2:
            per_jurisdiction_k = 1
        else:
            per_jurisdiction_k = requested_k
        for code in jurisdictions:
            section_hits = search(text, per_jurisdiction_k, code, section_task)
            per_jurisdiction.append({"jurisdiction": code, "sources": len(section_hits)})
            for hit in section_hits:
                source_id = hit.get("id")
                dedupe_key = (code, source_id) if source_id is not None else (
                    hit.get("title"), hit.get("jurisdiction"), hit.get("content", "")[:120]
                )
                if dedupe_key in seen_ids:
                    continue
                seen_ids.add(dedupe_key)
                hit = dict(hit)
                hit["matched_question"] = section.get("number")
                combined_hits.append(hit)

        retrieved_codes = [item["jurisdiction"] for item in per_jurisdiction if item["sources"]]
        missing_codes = [item["jurisdiction"] for item in per_jurisdiction if not item["sources"]]
        coverage.append({
            "question": section.get("number"),
            "title": section.get("title", ""),
            "jurisdictions_searched": jurisdictions,
            "jurisdictions_with_sources": retrieved_codes,
            "jurisdictions_without_sources": missing_codes,
            "status": "retrieved" if retrieved_codes and not missing_codes else
                      "partial" if retrieved_codes else "no_sources",
        })

    # Legal research takes precedence for a mixed prompt containing legal issues;
    # the specialist prompt then enforces source-backed answers and gap disclosure.
    legal_tasks = {
        "legal_research", "civil_procedure", "lawyer_assistance",
        "judicial_research", "document_review",
    }
    aggregate_task = "legal_research" if any(task in legal_tasks for task in section_tasks) else classify_task(question)
    return combined_hits[:24], coverage, aggregate_task


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


@app.get("/api/models")
def optional_models():
    from .optional_models import model_catalog
    return model_catalog()


class HFInferenceRequest(BaseModel):
    text: str = Field(min_length=1, max_length=12000)
    task: str = Field(default="sentiment-analysis", max_length=64)
    model: str | None = Field(default=None, max_length=256)
    candidate_labels: list[str] | None = Field(default=None, max_length=20)


@app.post("/api/models/huggingface")
def huggingface_inference(req: HFInferenceRequest):
    from .optional_models import run_hf_text
    try:
        return run_hf_text(req.text, req.task, req.model, req.candidate_labels)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503 if isinstance(exc, RuntimeError) else 400, detail=str(exc)) from exc


@app.post("/api/models/vision/{model_name}")
async def vision_inference(model_name: str, file: UploadFile = File(...)):
    if model_name not in {"mobilenet", "resnet50", "vgg16"}:
        raise HTTPException(status_code=404, detail="Unknown vision model")
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG or WebP image")
    payload = await file.read(8 * 1024 * 1024 + 1)
    if len(payload) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image exceeds 8 MB limit")
    try:
        from .optional_models import classify_image
        return {"model": model_name, "predictions": classify_image(model_name, payload)}
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503 if isinstance(exc, RuntimeError) else 400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Image could not be decoded or classified") from exc


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


@app.get("/api/coverage")
def legal_source_coverage():
    """Report source-registry presence without pretending it is corpus completeness."""
    registry = source_registry()
    by_jurisdiction = {}
    for item in registry.get("sources", []):
        code = str(item.get("jurisdiction", "GLOBAL")).upper()
        by_jurisdiction.setdefault(code, []).append({
            "name": item.get("name", "Unnamed source"),
            "url": item.get("url", ""),
            "type": item.get("type", "unspecified"),
            "authority": item.get("authority", "unspecified"),
        })
    jurisdictions_data = json.loads((Path(__file__).parent / "jurisdictions.json").read_text(encoding="utf-8"))
    rows = []
    for group in jurisdictions_data.get("groups", []):
        for item in group.get("items", []):
            code = str(item.get("code", "")).upper()
            sources = by_jurisdiction.get(code, [])
            rows.append({
                "code": code,
                "name": item.get("name", code),
                "registry_source_count": len(sources),
                "coverage_status": "official_or_listed_starting_points" if sources else "no_curated_source_registered",
                "sources": sources,
            })
    return {
        "coverage_scope": "Registry inventory only; does not prove that full text is indexed, current, comprehensive, or legally authoritative for every issue.",
        "jurisdictions": rows,
        "registered_source_count": sum(len(items) for items in by_jurisdiction.values()),
    }


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=14000)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    jurisdiction: str = Field(default="IN", min_length=1, max_length=80)
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
    clarification = clarification_for(question, req.jurisdiction)
    if clarification:
        return {
            "answer": (
                "I need one detail before I can answer accurately.\n\n"
                + clarification["question"]
                + "\n\nI will not assume which document, authority, or jurisdiction you mean."
            ),
            "citations": [],
            "model_connected": None,
            "model": {"provider": None, "model": None, "task": classify_task(question)},
            "jurisdiction": req.jurisdiction,
            "task": classify_task(question),
            "citation_validation": {"status": "not_applicable", "scope": "Clarification requested before research."},
            "quality": None,
            "quality_warning": "The question is underspecified; no legal conclusion has been generated.",
            "incomplete": False,
            "needs_clarification": True,
            "clarification": clarification,
        }
    if req.use_knowledge:
        hits, retrieval_coverage, task = _retrieve_request(question, req.jurisdiction, TOP_K)
    else:
        hits, retrieval_coverage, task = [], [], classify_task(question)
    legal_tasks = {"legal_research", "civil_procedure", "lawyer_assistance", "judicial_research", "document_review"}
    no_legal_source = req.use_knowledge and task in legal_tasks and not hits
    # Abstain only when a specific provision/case is asked about and nothing was retrieved;
    # broad conceptual questions get clearly labelled general information instead.
    if no_legal_source and names_specific_authority(question):
        return {
            "answer": (
                f"I could not retrieve a jurisdiction-matched legal source for {req.jurisdiction} that covers this question. "
                "To avoid guessing, I cannot give a source-backed answer about a specific provision or case from the current knowledge base. "
                "Add or locate the relevant official statute, regulation or judgment (Knowledge library), then retry."
            ),
            "citations": [],
            "model_connected": None,
            "model": {"provider": None, "model": None, "task": task},
            "jurisdiction": req.jurisdiction,
            "task": task,
            "retrieval_coverage": retrieval_coverage,
            "citation_validation": {
                "status": "no_retrieved_citations", "cited": [], "valid": [], "invalid": [],
                "paragraphs_checked": 0, "paragraphs_with_citations": 0, "uncited_paragraphs": 0,
                "coverage_status": "no_retrieved_sources",
                "scope": "No jurisdiction-matched source was retrieved; no legal conclusion was generated.",
            },
            "quality": None,
            "quality_warning": "No jurisdiction-matched legal source was retrieved. No legal conclusion was generated.",
            "incomplete": False,
            "needs_clarification": False,
            "clarification": None,
        }
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
    # Give the model a per-question coverage map. This is essential for mixed prompts:
    # it must answer supported parts and explicitly mark unsupported jurisdictions.
    if context and retrieval_coverage:
        coverage_lines = ["REQUEST ROUTING AND SOURCE COVERAGE (not legal authority):"]
        for item in retrieval_coverage:
            label = f"Question {item['question']}" if item.get("question") is not None else "Question"
            coverage_lines.append(
                f"{label}: searched {', '.join(item['jurisdictions_searched'])}; "
                f"sources found for {', '.join(item['jurisdictions_with_sources']) or 'none'}; "
                f"no sources for {', '.join(item['jurisdictions_without_sources']) or 'none'}."
            )
        coverage_lines.append(
            "Answer each question independently. Use retrieved sources only for propositions they support. "
            "For any jurisdiction or issue with no retrieved source, explicitly say it is not established by the indexed sources; do not fill the gap from memory."
        )
        context[0] = "\n".join(coverage_lines) + "\n\n" + context[0]

    # Expose only the sources the model actually receives; otherwise the UI would
    # list (and the validator would accept) citations the model never saw.
    context_text, included = fit_context(context)
    citations = citations[:included]
    answer, error, model_info = generate(messages, context_text, [c["label"] for c in citations])
    if error:
        answer = "ARLAW could not connect to any configured AI provider.\n\n" + error
    quality_warning = model_info.get("quality_warning")
    if no_legal_source and not error:
        quality_warning = ("No jurisdiction-matched source was retrieved; this is general, unverified information. "
                           + (quality_warning or "")).strip()
    return {
        "answer": answer,
        "citations": citations,
        "model_connected": error is None,
        "model": model_info,
        "jurisdiction": req.jurisdiction,
        "retrieval_coverage": retrieval_coverage,
        "task": model_info.get("task"),
        "citation_validation": model_info.get("citation_validation"),
        "quality": model_info.get("quality"),
        "quality_warning": quality_warning,
        "incomplete": model_info.get("incomplete", False),
        "needs_clarification": False,
        "clarification": None,
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
    jurisdiction: str = Form("IN"),
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
