import sqlite3
import re
from .config import DB_PATH

def connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.execute("CREATE TABLE IF NOT EXISTS sources (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, jurisdiction TEXT NOT NULL DEFAULT 'GLOBAL', source_url TEXT DEFAULT '', as_of TEXT DEFAULT '', file_name TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP, category TEXT DEFAULT 'general')")
        cols = {r[1] for r in c.execute("PRAGMA table_info(sources)").fetchall()}
        for name, definition in [("authority", "TEXT DEFAULT 'unspecified'"), ("language", "TEXT DEFAULT 'und'")]:
            if name not in cols:
                c.execute(f"ALTER TABLE sources ADD COLUMN {name} {definition}")
        if "category" not in cols:
            c.execute("ALTER TABLE sources ADD COLUMN category TEXT DEFAULT 'general'")
        # Backfill rows created by earlier releases without changing user-uploaded sources.
        c.execute("UPDATE sources SET category='law' WHERE file_name='bundled-curated-digest'")
        c.execute("UPDATE sources SET category='economy' WHERE file_name='bundled-curated-digest' AND (lower(title) LIKE '%economic change%' OR lower(title) LIKE '%food,%' OR lower(title) LIKE '%energy and critical%' OR lower(title) LIKE '%macroeconomic%' OR lower(title) LIKE '%trade, logistics%')")
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

def infer_category(title="", text="", file_name=""):
    """Conservative source category used to keep unrelated bundled material out of retrieval."""
    label = f"{title} {file_name}".lower()
    economic_markers = ("economic change", "food, agriculture", "food-shortage", "energy and critical",
                        "macroeconomic", "trade, logistics", "shortage monitoring", "supply-chain")
    if any(marker in label for marker in economic_markers):
        return "economy"
    if file_name == "bundled-curated-digest":
        return "law"
    return "general"


def add_source(title, text, jurisdiction="GLOBAL", source_url="", as_of="", file_name="", authority="unspecified", language="und", category=None):
    parts = split_text(text)
    if not parts: raise ValueError("No readable text found.")
    category = (category or infer_category(title, text, file_name)).lower()
    if category not in {"law", "economy", "general"}:
        category = "general"
    with connect() as c:
        cur = c.execute("INSERT INTO sources(title,jurisdiction,source_url,as_of,file_name,authority,language,category) VALUES(?,?,?,?,?,?,?,?)",
            (title, jurisdiction.upper(), source_url, as_of, file_name, authority, language, category))
        sid = cur.lastrowid
        c.executemany("INSERT INTO chunks(source_id,chunk_no,content) VALUES(?,?,?)", [(sid,i,x) for i,x in enumerate(parts)])
    return {"id": sid, "chunks": len(parts)}

_AUTHORITY_PRIORITY = {
    "official": 4,
    "official primary source": 4,
    "primary": 4,
    "primary source": 4,
    "court": 3,
    "regulator": 3,
    "official secondary": 2,
    "case-law repository": 2,
    "case law repository": 2,
    "secondary": 1,
    "unspecified": 0,
}

_LEGAL_TASKS = {
    "legal_research", "civil_procedure", "lawyer_assistance",
    "judicial_research", "document_review",
}


def _authority_priority(authority):
    """Rank declared metadata only; this does not independently verify a source."""
    label = " ".join(str(authority or "unspecified").strip().lower().split())
    return _AUTHORITY_PRIORITY.get(label, 0)


def search(query, top_k=6, jurisdiction="GLOBAL", task=None):
    """Retrieve relevant sources with conservative legal-jurisdiction boundaries.

    Legal tasks require an exact jurisdiction match. GLOBAL and INTL sources
    are not silently mixed into domestic legal research. Non-legal research
    may use global/international context, explicitly labelled as such.
    Authority ranking uses declared metadata, not independent verification.
    """
    stop = {
        "the", "and", "for", "with", "from", "that", "this", "what", "when",
        "where", "who", "does", "have", "has", "are", "was", "were", "into",
        "about", "explain", "under", "between", "both", "their", "them",
        "your", "you", "how", "why", "which", "article", "section", "act",
        "case", "law"
    }
    terms = []
    for token in re.findall(r"[\w]+", (query or "").lower(), flags=re.UNICODE):
        if len(token) > 1 and token not in stop and token not in terms:
            terms.append(token)

    if not terms:
        return []

    terms = terms[:16]
    expr = " OR ".join('"' + t.replace('"', '""') + '"' for t in terms)
    j = (jurisdiction or "GLOBAL").upper().strip()
    task = (task or "general").lower()
    legal_task = task in _LEGAL_TASKS

    allowed_categories = (
        {"law", "general"} if legal_task
        else {"economy", "general"}
        if task in {"finance_tax", "accounting", "ca_tax"}
        else {"law", "economy", "general"}
    )

    candidate_limit = max(60, top_k * 30)

    with connect() as c:
        base_sql = (
            "SELECT s.id,s.title,s.jurisdiction,s.source_url,s.as_of,"
            "s.authority,s.language,s.category,c.chunk_no,c.content,bm25(chunks) score "
            "FROM chunks c JOIN sources s ON s.id=c.source_id "
        )

        if legal_task:
            rows = c.execute(
                base_sql +
                "WHERE chunks MATCH ? "
                "AND UPPER(TRIM(COALESCE(s.jurisdiction, 'GLOBAL'))) = ? "
                "ORDER BY score LIMIT ?",
                (expr, j, candidate_limit)
            ).fetchall()
        else:
            rows = c.execute(
                base_sql +
                "WHERE chunks MATCH ? ORDER BY score LIMIT ?",
                (expr, candidate_limit)
            ).fetchall()

    best_by_source = {}
    for row in rows:
        h = dict(row)
        source_j = (h.get("jurisdiction") or "GLOBAL").upper().strip()

        if legal_task:
            if source_j != j:
                continue
            jurisdiction_relation = "exact"
        else:
            if source_j not in {j, "GLOBAL", "INTL"}:
                continue
            jurisdiction_relation = (
                "exact" if source_j == j
                else "international_context" if source_j == "INTL"
                else "global_context"
            )

        category = (
            h.get("category")
            or infer_category(h["title"], h["content"], "")
        ).lower()
        if category not in allowed_categories:
            continue

        haystack = (h["title"] + " " + h["content"]).lower()
        matched = sum(1 for term in terms if term in haystack)
        minimum = 1 if len(terms) <= 2 else 2
        if matched < minimum:
            continue

        coverage = matched / len(terms)
        title_hits = sum(1 for term in terms if term in h["title"].lower())
        jurisdiction_bonus = (
            0.08
            if jurisdiction_relation == "exact" and j not in {"GLOBAL", "INTL"}
            else 0.0
        )
        h["relevance"] = round(
            coverage + min(title_hits, 3) * 0.04 + jurisdiction_bonus, 4
        )
        h["authority_priority"] = _authority_priority(h.get("authority"))
        h["jurisdiction_relation"] = jurisdiction_relation
        h["ranking_score"] = round(
            h["relevance"] + h["authority_priority"] * 0.10, 4
        )

        previous = best_by_source.get(h["id"])
        if previous is None or (
            h["ranking_score"], h["relevance"], -float(h["score"])
        ) > (
            previous["ranking_score"], previous["relevance"],
            -float(previous["score"])
        ):
            h["category"] = category
            best_by_source[h["id"]] = h

    ranked = sorted(
        best_by_source.values(),
        key=lambda h: (
            h["ranking_score"], h["relevance"], -float(h["score"])
        ),
        reverse=True,
    )
    return ranked[:max(1, min(int(top_k), 20))]



def list_sources():
    with connect() as c:
        return [dict(r) for r in c.execute("SELECT id,title,jurisdiction,source_url,as_of,file_name,authority,language,category,created_at FROM sources ORDER BY id DESC").fetchall()]


def seed_builtin_knowledge():
    """Load the bundled, clearly-labelled educational digests once per source title."""
    import json
    from pathlib import Path
    seed_path = Path(__file__).with_name("builtin_knowledge.json")
    if not seed_path.exists():
        return 0
    records = json.loads(seed_path.read_text(encoding="utf-8"))
    inserted = 0
    with connect() as c:
        existing = {r[0] for r in c.execute("SELECT title FROM sources").fetchall()}
    for item in records:
        if item["title"] in existing:
            continue
        add_source(item["title"], item["text"], item.get("jurisdiction", "GLOBAL"),
                   item.get("source_url", ""), item.get("as_of", ""),
                   item.get("file_name", "bundled-curated-digest"), item.get("authority", "secondary"),
                   item.get("language", "en"), item.get("category"))
        inserted += 1
    return inserted
