from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
import hashlib, json
from .config import STATIC_DIR, UPLOAD_DIR, TOP_K, OLLAMA_BASE_URL, OLLAMA_MODEL
from .knowledge import init_db, add_source, search, list_sources
from .llm import generate

app = FastAPI(title="ARLAW AI Global", version="1.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def startup(): init_db()

@app.get("/")
def home(): return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
def health(): return {"status":"ok","product":"ARLAW AI Global","version":"1.0.0","mode":"local-first"}

@app.get("/api/health/model")
def model_health():
    import requests
    try:
        r=requests.get(f"{OLLAMA_BASE_URL}/api/tags",timeout=3); r.raise_for_status()
        names=[m.get("name") for m in r.json().get("models",[])]
        return {"ollama":"reachable","configured_model":OLLAMA_MODEL,"model_installed":OLLAMA_MODEL in names,"available_models":names}
    except requests.RequestException:
        return {"ollama":"not_reachable","configured_model":OLLAMA_MODEL}

@app.get("/api/jurisdictions")
def jurisdictions():
    return json.loads((Path(__file__).parent/"jurisdictions.json").read_text(encoding="utf-8"))

@app.get("/api/registry")
def source_registry():
    return json.loads((Path(__file__).parent/"sources_registry.json").read_text(encoding="utf-8"))

class ChatRequest(BaseModel):
    messages: list[dict] = Field(min_length=1,max_length=30)
    jurisdiction: str = "GLOBAL"
    use_knowledge: bool = True

@app.post("/api/chat")
def chat(req: ChatRequest):
    last=next((m for m in reversed(req.messages) if m.get("role")=="user"),None)
    if not last: raise HTTPException(400,"A user message is required.")
    question=str(last.get("content",""))[:14000]
    hits=search(question,TOP_K,req.jurisdiction) if req.use_knowledge else []
    context=[]; citations=[]
    for i,h in enumerate(hits,1):
        label=f"S{i}"
        context.append(f"[{label}] {h['title']} | Jurisdiction: {h['jurisdiction']} | Authority: {h['authority']} | Language: {h['language']} | As of: {h['as_of'] or 'not supplied'} | URL: {h['source_url'] or 'not supplied'}\n{h['content']}")
        citations.append({"label":label,"title":h["title"],"jurisdiction":h["jurisdiction"],"authority":h["authority"],"language":h["language"],"as_of":h["as_of"],"url":h["source_url"]})
    answer,error=generate(req.messages,"\n\n".join(context))
    if error: answer="ARLAW cannot generate an AI answer because its local model is disconnected.\n\n"+error
    return {"answer":answer,"citations":citations,"model_connected":error is None,"jurisdiction":req.jurisdiction}

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
