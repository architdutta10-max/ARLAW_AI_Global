from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
from contextlib import asynccontextmanager
import hashlib, json
from .config import STATIC_DIR, UPLOAD_DIR, TOP_K
from .knowledge import init_db, add_source, search, list_sources, seed_builtin_knowledge
from .llm import generate, provider_order, classify_task

@asynccontextmanager
async def lifespan(app):
    init_db()
    seed_builtin_knowledge()
    yield

app = FastAPI(title="ARLAW AI Global", version="2.4.0", description="Hybrid AI research and professional-workflow support platform", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def home(): return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
def health(): return {"status":"ok","product":"ARLAW AI Global","version":"2.4.0","mode":"local-and-cloud-hybrid","disclaimer":"Research and workflow assistance only; not professional representation, certification or judicial decision-making."}

@app.get("/api/capabilities")
def capabilities():
    return {
        "professional_workspaces": [
            {"id":"lawyer_assistance","name":"Lawyer & Advocate Assistance","scope":"Research, issue spotting, drafting support and matter organisation","boundary":"Does not represent clients or certify court filings."},
            {"id":"accounting","name":"Accounting Support","scope":"Bookkeeping explanations, reconciliations and financial statement analysis","boundary":"Does not certify accounts or conduct statutory audits."},
            {"id":"ca_tax","name":"CA & Tax Support","scope":"Tax research, worked calculations and compliance preparation","boundary":"Does not sign, attest, certify or conduct regulated audits."},
            {"id":"judicial_research","name":"Judicial Research Support","scope":"Neutral issue, evidence and precedent organisation","boundary":"Does not determine guilt, liability, credibility or case outcomes."},
            {"id":"legal_research","name":"Legal Research","scope":"Jurisdiction-aware legal information and source-grounded research","boundary":"Not a substitute for qualified legal advice."}
        ],
        "supported_languages_prompted": ["English", "Hindi", "Bengali", "other languages when supported by the configured model"],
        "verification": "Citation labels are checked for existence only; source support, currency and legal correctness require human verification."
    }

@app.get("/api/health/model")
def model_health():
    import os
    providers = provider_order()
    return {"providers": providers, "primary_provider": providers[0] if providers else None,
            "groq_configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
            "ollama_enabled": os.getenv("OLLAMA_ENABLED", "true").lower() in {"1", "true", "yes", "on"},
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            "ollama_model": os.getenv("OLLAMA_MODEL", "qwen3:8b"),
            "local_models": True, "multi_model_review": False}

@app.get("/api/jurisdictions")
def jurisdictions():
    return json.loads((Path(__file__).parent/"jurisdictions.json").read_text(encoding="utf-8"))

@app.get("/api/registry")
def source_registry():
    return json.loads((Path(__file__).parent/"sources_registry.json").read_text(encoding="utf-8"))

class ChatMessage(BaseModel):
    role: str
    content: str = Field(min_length=1, max_length=14000)

class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    jurisdiction: str = Field(default="GLOBAL", min_length=1, max_length=80)
    use_knowledge: bool = True

@app.post("/api/chat")
def chat(req: ChatRequest):
    messages = [m.model_dump() for m in req.messages]
    if any(m["role"] not in {"user", "assistant"} for m in messages):
        raise HTTPException(422, "Only user and assistant message roles are accepted.")
    last=next((m for m in reversed(messages) if m.get("role")=="user"),None)
    if not last: raise HTTPException(400,"A user message is required.")
    question=last["content"]
    hits=search(question,TOP_K,req.jurisdiction, classify_task(question)) if req.use_knowledge else []
    context=[]; citations=[]
    for i,h in enumerate(hits,1):
        label=f"S{i}"
        context.append(f"[{label}] {h['title']} | Jurisdiction: {h['jurisdiction']} | Jurisdiction relationship: {h.get('jurisdiction_relation', 'unspecified')} | Declared authority: {h['authority']} (ranking priority {h.get('authority_priority', 0)}; not independently verified) | Language: {h['language']} | Recorded date: {h['as_of'] or 'not supplied'} (does not establish current validity) | URL: {h['source_url'] or 'not supplied'}\n{h['content']}")
        citations.append({"label":label,"title":h["title"],"jurisdiction":h["jurisdiction"],"jurisdiction_relation":h.get("jurisdiction_relation", "unspecified"),"authority":h["authority"],"authority_priority":h.get("authority_priority", 0),"language":h["language"],"category":h.get("category", "general"),"retrieval_relevance":h.get("relevance"),"as_of":h["as_of"],"url":h["source_url"]})
    answer,error,model_info=generate(messages,"\n\n".join(context),[c["label"] for c in citations])
    if error: answer="ARLAW could not connect to any configured AI provider.\n\n"+error
    return {"answer":answer,"citations":citations,"model_connected":error is None,"model":model_info,"jurisdiction":req.jurisdiction,"task":model_info.get("task"),"citation_validation":model_info.get("citation_validation"),"quality":model_info.get("quality"),"quality_warning":model_info.get("quality_warning"),"incomplete":model_info.get("incomplete", False)}

@app.post("/api/documents")
async def upload_document(file: UploadFile=File(...), title: str=Form(""), jurisdiction: str=Form("GLOBAL"),
    source_url: str=Form(""), as_of: str=Form(""), authority: str=Form("unspecified"), language: str=Form("und")):
    name=Path(file.filename or "upload").name; suffix=Path(name).suffix.lower()
    if suffix not in {".txt",".md",".pdf"}: raise HTTPException(415,"Only .txt, .md and text-based .pdf are supported.")
    raw=await file.read()
    if len(raw)>20*1024*1024: raise HTTPException(413,"Maximum upload size is 20 MB.")
    if suffix==".pdf":
        try:
            from pypdf import PdfReader
            import io
            text="\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(raw)).pages)
        except Exception: raise HTTPException(400,"Could not extract text from PDF.")
    else: text=raw.decode("utf-8",errors="replace")
    if len(text.strip())<40: raise HTTPException(400,"Too little extractable text. Scanned PDFs need OCR before upload.")
    safe=hashlib.sha256(raw).hexdigest()[:12]+"_"+name
    (UPLOAD_DIR/safe).write_bytes(raw)
    result=add_source(title.strip() or name,text,jurisdiction,source_url,as_of,safe,authority,language)
    return {"message":"Indexed locally","file":safe,**result}

@app.get("/api/sources")
def sources(): return {"sources":list_sources()}
