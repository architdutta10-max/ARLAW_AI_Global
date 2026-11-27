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
        # A generic institution homepage is not a document-level citation URL.
        for sid, url in c.execute("SELECT id, source_url FROM sources WHERE COALESCE(source_url,'')<>''").fetchall():
            if not _specific_source_url(url):
                c.execute("UPDATE sources SET source_url='' WHERE id=?", (sid,))
        c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(source_id UNINDEXED, chunk_no UNINDEXED, content, tokenize='unicode61')")

def _specific_source_url(source_url):
    """Reject generic organisation homepages as if they were document-level citations."""
    from urllib.parse import urlparse
    value = (source_url or "").strip()
    if not value:
        return ""
    try:
        parsed = urlparse(value)
    except ValueError:
        return ""
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    if not (parsed.path or "").strip("/") and not parsed.query:
        return ""
    return value


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
    source_url = _specific_source_url(source_url)
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


def _expand_anchored_provision(source_id, chunk_no, content, heading_start, provision_number):
    """Reassemble a complete numbered provision from overlapping FTS chunks.

    Statutory provisions often exceed one 1,200-character chunk. Returning only
    the chunk containing the heading can expose the definition while dropping
    the punishment or proviso. Expand from the matched heading until the next
    numbered statutory heading, preserving the indexed text and overlap.
    """
    try:
        start_index = int(chunk_no)
    except (TypeError, ValueError):
        return content

    with connect() as conn:
        rows = conn.execute(
            "SELECT chunk_no,content FROM chunks WHERE source_id=? "
            "AND CAST(chunk_no AS INTEGER)>=? "
            "ORDER BY CAST(chunk_no AS INTEGER) LIMIT 16",
            (source_id, start_index),
        ).fetchall()

    if not rows:
        return content

    first = str(rows[0]["content"])
    if not (0 <= heading_start < len(first)):
        return content
    merged = first[heading_start:]
    previous_full_chunk = first

    next_heading = re.compile(
        r"(?<![0-9A-Za-z])(\d{1,4})\.\s+[A-Z][^—]{1,100}?\s*—"
    )
    initial_heading = next_heading.search(merged)
    search_from = initial_heading.end() if initial_heading else 0
    for row in rows[1:]:
        part = str(row["content"])
        overlap = 0
        for size in range(min(300, len(previous_full_chunk), len(part)), 0, -1):
            if previous_full_chunk[-size:] == part[:size]:
                overlap = size
                break
        addition = part[overlap:] if overlap else " " + part
        merged += addition
        previous_full_chunk = part
        following = next_heading.search(merged, pos=search_from)
        if following and following.group(1) != str(provision_number):
            merged = merged[:following.start()].rstrip()
            break

    return merged.strip() or content


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
        "case", "law", "of", "cite", "cited", "citation", "citations",
        "authoritative", "legal", "sources", "source", "united", "states",
        "india", "constitution"
    }
    terms = []
    for token in re.findall(r"[\w]+", (query or "").lower(), flags=re.UNICODE):
        if len(token) > 1 and token not in stop and token not in terms:
            terms.append(token)

    if not terms:
        return []

    # Expand common fact descriptions into legal concepts already used by the
    # jurisdiction-specific digests. This is retrieval assistance, not a legal
    # conclusion: the model still has to support every proposition from excerpts.
    query_lower = (query or "").lower()
    expansions = []
    if re.search(r"\b(conceal(?:s|ed|ing|ment)?|falsif(?:y|ies|ied|ication)|false accounts?)\b", query_lower):
        expansions.extend(["fraud", "concealment", "false", "statements", "deceive"])
    if re.search(r"\b(transfers?|diverts?|misappropriat(?:e|es|ed|ion)?)\b", query_lower) and re.search(r"\bassets?\b", query_lower):
        expansions.extend(["misappropriation", "undue", "advantage", "abuse", "position"])
    # Indian statutory aliases: add the full instrument names and topic vocabulary
    # so acronyms, colloquial references and former-code terminology converge.
    statute_aliases = {
        "bns": [r"\bbns\b", r"bharatiya nyaya sanhita", r"new penal code"],
        "bnss": [r"\bbnss\b", r"bharatiya nagarik suraksha sanhita", r"new criminal procedure"],
        "bsa": [r"\bbsa\b", r"bharatiya sakshya adhiniyam", r"new evidence law"],
        "dpdp": [r"\bdpdp\b", r"digital personal data protection"],
        "limitation": [r"limitation act", r"period of limitation", r"schedule article"],
        "contract": [r"indian contract act", r"contract act"],
        "income_tax_2025": [r"income[- ]tax act,? 2025", r"tax year 2026[-–]27", r"income tax act 2025"],
    }
    for alias, patterns in statute_aliases.items():
        if any(re.search(pattern, query_lower, re.I) for pattern in patterns):
            expansions.append(alias)
    if re.search(r"\b(?:ipc|indian penal code)\b", query_lower):
        expansions.extend(["bns", "bharatiya", "nyaya", "sanhita", "repeal", "savings"])
    if re.search(r"\b(?:crpc|code of criminal procedure)\b", query_lower):
        expansions.extend(["bnss", "nagarik", "suraksha", "sanhita", "repeal", "savings"])
    if re.search(r"\b(?:indian evidence act|evidence act)\b", query_lower):
        expansions.extend(["bsa", "sakshya", "adhiniyam", "electronic", "digital"])
    if re.search(r"\b(?:dpdp|digital personal data protection)\b", query_lower):
        expansions.extend(["act", "rules", "commencement", "notification", "gazette", "843", "846"])
    if re.search(r"\b(?:limitation act|limitation period|schedule article)\b", query_lower):
        expansions.extend(["schedule", "suits", "appeals", "applications", "article", "prescribed", "period"])
    if re.search(r"\b(?:contract act|indian contract act)\b", query_lower):
        expansions.extend(["proposal", "acceptance", "consideration", "consent", "coercion", "fraud", "mistake", "lawful", "object"])
    if re.search(r"\b(?:tax year 2026[-–]27|income[- ]tax act,? 2025|income tax 2026[-–]27)\b", query_lower):
        expansions.extend(["income-tax", "2025", "2026", "rules", "2026", "forms", "CBDT"])
    for token in expansions:
        if token not in terms:
            terms.append(token)
    terms = terms[:32]  # Keep named authorities appearing later in long, structured prompts.

    # Extract explicit legal anchors. Generic token overlap is not enough for a
    # question about a numbered provision: "21" can occur in dates, footnotes
    # and unrelated constitutional articles.
    provision_anchors = [
        (kind.lower(), number.upper())
        for kind, number in re.findall(
            r"\b(article|art\.?|section|sec\.?)\s+(\d+[a-z]?)\b",
            query or "", flags=re.IGNORECASE
        )
    ]

    # If a question names a particular statute and a numbered provision,
    # prevent same-numbered provisions from unrelated Acts entering results.
    required_source_patterns = []
    if re.search(
        r"\b(?:bns|bharatiya nyaya sanhita|new penal code)\b",
        query_lower, flags=re.IGNORECASE
    ):
        required_source_patterns.append(
            r"\b(?:bharatiya nyaya sanhita|bns)\b"
        )
    if re.search(
        r"\b(?:indian\s+)?contract act\b",
        query_lower, flags=re.IGNORECASE
    ):
        required_source_patterns.append(
            r"\b(?:indian\s+)?contract act\b"
        )
    amendment_anchors = [
        " ".join(match.lower().split())
        for match in re.findall(
            r"\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|"
            r"tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|"
            r"seventeenth|eighteenth|nineteenth|twentieth)\s+amendment\b",
            query or "", flags=re.IGNORECASE
        )
    ]

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

    candidate_limit = max(2000, top_k * 100) if provision_anchors else max(60, top_k * 30)

    with connect() as c:
        base_sql = (
            "SELECT s.id,s.title,s.jurisdiction,s.source_url,s.as_of,s.file_name,"
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

        # Do not let a bundled full statute compete with focused sources
        # for unrelated legal questions. Full texts remain eligible when
        # the query explicitly identifies the corresponding statute.
        if (
            legal_task
            and str(h.get("file_name") or "").startswith("official-refresh:")
            and not required_source_patterns
        ):
            continue

        # A named statute plus a numbered provision is a source constraint,
        # not merely a keyword preference. Do not accept another Act's
        # coincidentally numbered provision or an unrelated judgment.
        if legal_task and provision_anchors and required_source_patterns:
            if not any(
                re.search(pattern, h["title"], flags=re.IGNORECASE)
                for pattern in required_source_patterns
            ):
                continue

        # Explicit ordinal amendments must be present in the retrieved passage.
        # This prevents a generic constitutional case digest from being passed
        # off as authority for (for example) the First Amendment.
        if amendment_anchors and not all(anchor in haystack for anchor in amendment_anchors):
            continue

        provision_matches = 0
        provision_heading_matches = 0
        matched_heading_start = None
        matched_heading_number = None
        for kind, number in provision_anchors:
            if kind in {"article", "art", "art."}:
                reference_pattern = rf"\b(?:article|arts?\.?)[ \t]*{re.escape(number)}\b"
            else:
                reference_pattern = rf"\b(?:section|sec|sec\.?)[ \t]*{re.escape(number)}\b"
            referenced = bool(re.search(reference_pattern, haystack, flags=re.IGNORECASE))
            # Official legislative texts commonly print a provision as
            # "21. Protection of life..." without repeating the word Article.
            heading_pattern = re.compile(
                rf"(?<![0-9A-Za-z]){re.escape(number)}\.\s+([^—]{{2,100}}?)\s*[.]?\s*—"
            )
            heading = False
            for heading_match in heading_pattern.finditer(h["content"]):
                heading_text = heading_match.group(1).strip()
                preceding_context = h["content"][max(0, heading_match.start() - 180):heading_match.start()]
                if (
                    not re.search(
                        r"\b(amendment|schedule|appendix|entry|entries|list|act)\b",
                        heading_text, flags=re.IGNORECASE
                    )
                    and not re.search(r"\b(schedule|appendix)\b", preceding_context, flags=re.IGNORECASE)
                ):
                    heading = True
                    matched_heading_start = heading_match.start()
                    matched_heading_number = number
                    break
            if referenced or heading:
                provision_matches += 1
                if heading:
                    provision_heading_matches += 1
        if provision_anchors and provision_matches == 0:
            continue

        matched = sum(1 for term in terms if term in haystack)
        # Require stronger overlap for multi-term legal questions. This avoids
        # returning unrelated case digests merely because they mention generic
        # words such as "United States" or "constitution". Empty retrieval is
        # safer than presenting weak matches as legal support.
        minimum = 1 if provision_anchors or len(terms) <= 2 else min(3, len(terms))
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
        provision_bonus = (
            0.55 * provision_matches + 1.50 * provision_heading_matches
            if provision_anchors else 0.0
        )
        h["provision_matches"] = provision_matches
        h["provision_heading_matches"] = provision_heading_matches
        if matched_heading_start is not None and matched_heading_number is not None:
            h["content"] = _expand_anchored_provision(
                h["id"], h["chunk_no"], h["content"],
                matched_heading_start, matched_heading_number,
            )
        h["ranking_score"] = round(
            h["relevance"] + h["authority_priority"] * 0.10 + provision_bonus, 4
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
    """Insert bundled sources and keep only bundled records synchronized with JSON.

    User-uploaded sources are never overwritten. Existing bundled records have
    their metadata refreshed, and their FTS chunks are replaced only when the
    bundled text actually changes.
    """
    import json
    from pathlib import Path

    seed_path = Path(__file__).with_name("builtin_knowledge.json")
    if not seed_path.exists():
        return 0
    records = json.loads(seed_path.read_text(encoding="utf-8"))
    inserted = 0

    with connect() as c:
        for item in records:
            title = str(item["title"]).strip()
            jurisdiction = str(item.get("jurisdiction", "GLOBAL")).upper().strip()
            file_name = str(item.get("file_name", "bundled-curated-digest"))
            authority = str(item.get("authority", "secondary"))
            language = str(item.get("language", "en"))
            category = (item.get("category") or infer_category(
                title, item.get("text", ""), file_name
            )).lower()
            if category not in {"law", "economy", "general"}:
                category = "general"
            source_url = _specific_source_url(item.get("source_url", ""))
            as_of = str(item.get("as_of", ""))
            parts = split_text(str(item.get("text", "")))
            if not parts:
                continue

            existing = c.execute(
                "SELECT id,file_name FROM sources WHERE title=? ORDER BY id LIMIT 1",
                (title,),
            ).fetchone()
            if existing is None:
                cur = c.execute(
                    "INSERT INTO sources(title,jurisdiction,source_url,as_of,file_name,authority,language,category) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (title, jurisdiction, source_url, as_of, file_name,
                     authority, language, category),
                )
                source_id = cur.lastrowid
                c.executemany(
                    "INSERT INTO chunks(source_id,chunk_no,content) VALUES(?,?,?)",
                    [(source_id, i, part) for i, part in enumerate(parts)],
                )
                inserted += 1
                continue

            # Never replace a user-uploaded or independently ingested source
            # merely because its title matches a bundled record. Seeded records
            # must also retain the exact managed file_name from the JSON manifest.
            if existing["file_name"] != file_name:
                continue

            source_id = existing["id"]
            old_parts = [r[0] for r in c.execute(
                "SELECT content FROM chunks WHERE source_id=? ORDER BY CAST(chunk_no AS INTEGER)",
                (source_id,),
            ).fetchall()]
            if old_parts != parts:
                c.execute("DELETE FROM chunks WHERE source_id=?", (source_id,))
                c.executemany(
                    "INSERT INTO chunks(source_id,chunk_no,content) VALUES(?,?,?)",
                    [(source_id, i, part) for i, part in enumerate(parts)],
                )
            c.execute(
                "UPDATE sources SET jurisdiction=?,source_url=?,as_of=?,authority=?,language=?,category=? "
                "WHERE id=? AND file_name=?",
                (jurisdiction, source_url, as_of, authority, language, category, source_id, file_name),
            )
    return inserted
