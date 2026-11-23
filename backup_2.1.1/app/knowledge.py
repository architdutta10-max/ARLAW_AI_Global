import sqlite3
from .config import DB_PATH

def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.execute("CREATE TABLE IF NOT EXISTS sources (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, jurisdiction TEXT NOT NULL DEFAULT 'GLOBAL', source_url TEXT DEFAULT '', as_of TEXT DEFAULT '', file_name TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        cols = {r[1] for r in c.execute("PRAGMA table_info(sources)").fetchall()}
        for name, definition in [("authority", "TEXT DEFAULT 'unspecified'"), ("language", "TEXT DEFAULT 'und'")]:
            if name not in cols:
                c.execute(f"ALTER TABLE sources ADD COLUMN {name} {definition}")
        c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(source_id UNINDEXED, chunk_no UNINDEXED, content, tokenize='unicode61')")

def split_text(text, size=1200, overlap=180):
    text = " ".join(text.split())
    out, start = [], 0
    while start < len(text):
        end = min(len(text), start + size)
        out.append(text[start:end])
        if end == len(text): break
        start = max(start + 1, end - overlap)
    return out

def add_source(title, text, jurisdiction="GLOBAL", source_url="", as_of="", file_name="", authority="unspecified", language="und"):
    parts = split_text(text)
    if not parts: raise ValueError("No readable text found.")
    with connect() as c:
        cur = c.execute("INSERT INTO sources(title,jurisdiction,source_url,as_of,file_name,authority,language) VALUES(?,?,?,?,?,?,?)",
            (title, jurisdiction.upper(), source_url, as_of, file_name, authority, language))
        sid = cur.lastrowid
        c.executemany("INSERT INTO chunks(source_id,chunk_no,content) VALUES(?,?,?)", [(sid,i,x) for i,x in enumerate(parts)])
    return {"id": sid, "chunks": len(parts)}

def search(query, top_k=6, jurisdiction="GLOBAL"):
    terms = [t for t in query.replace('"',' ').split() if len(t)>1]
    if not terms: return []
    expr = " OR ".join('"'+t.replace('"','""')+'"' for t in terms[:16])
    with connect() as c:
        rows = c.execute("SELECT s.id,s.title,s.jurisdiction,s.source_url,s.as_of,s.authority,s.language,c.chunk_no,c.content,bm25(chunks) score FROM chunks c JOIN sources s ON s.id=c.source_id WHERE chunks MATCH ? ORDER BY score LIMIT ?", (expr,top_k*12)).fetchall()
    hits = [dict(r) for r in rows]
    j = (jurisdiction or "GLOBAL").upper()
    preferred = [h for h in hits if h["jurisdiction"] in {j,"GLOBAL","INTL"}]
    return (preferred or hits)[:top_k]

def list_sources():
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT id,title,jurisdiction,source_url,as_of,file_name,authority,language,created_at FROM sources ORDER BY id DESC").fetchall()]
