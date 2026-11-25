"""Explicitly refresh ARLAW's India primary-law corpus from fixed official URLs.

Run: python scripts/refresh_indian_legal_corpus.py
This script never runs automatically at web-service startup. It only fetches the
fixed allowlisted documents in app/indian_legal_sources.json.
"""
from __future__ import annotations
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import requests
from pypdf import PdfReader
from io import BytesIO

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "app" / "indian_legal_sources.json"
ALLOWED_HOSTS = {"www.indiacode.nic.in", "indiacode.nic.in", "www.meity.gov.in", "meity.gov.in", "www.incometax.gov.in"}
MAX_BYTES = 45 * 1024 * 1024


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip += 1
        elif tag in {"p", "div", "li", "h1", "h2", "h3", "tr", "br"} and not self.skip:
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"} and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(data.strip())


def extract_document(item):
    url = item["url"]
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError(f"Blocked non-allowlisted source: {url}")
    response = requests.get(url, timeout=(15, 90), headers={"User-Agent": "ARLAW-AI-legal-corpus-refresh/3.2.0"}, stream=True)
    response.raise_for_status()
    chunks, total = [], 0
    for block in response.iter_content(1024 * 256):
        if not block:
            continue
        total += len(block)
        if total > MAX_BYTES:
            raise ValueError(f"Document exceeds {MAX_BYTES} byte safety limit: {item['key']}")
        chunks.append(block)
    raw = b"".join(chunks)
    if item["format"] == "pdf":
        reader = PdfReader(BytesIO(raw))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        parser = TextExtractor()
        parser.feed(raw.decode(response.encoding or "utf-8", errors="replace"))
        text = "\n".join(parser.parts)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < 500:
        raise ValueError(f"Extracted text too short; refusing to replace indexed source: {item['key']}")
    return text, len(raw)


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # Add project root so this script also works when invoked from another cwd.
    sys.path.insert(0, str(ROOT))
    from app import knowledge
    knowledge.init_db()
    results = []
    for item in manifest["sources"]:
        try:
            text, byte_count = extract_document(item)
            managed_name = f"official-refresh:{item['key']}"
            # Replace only the exact row previously created by this script.
            with knowledge.connect() as conn:
                old = conn.execute("SELECT id FROM sources WHERE file_name=?", (managed_name,)).fetchall()
                for row in old:
                    conn.execute("DELETE FROM chunks WHERE source_id=?", (row["id"],))
                    conn.execute("DELETE FROM sources WHERE id=?", (row["id"],))
            result = knowledge.add_source(
                title=item["title"], text=text, jurisdiction=item["jurisdiction"],
                source_url=item["url"], as_of=item.get("as_of", ""),
                file_name=managed_name, authority=item.get("authority", "official primary source"),
                language="en", category="law",
            )
            results.append({"key": item["key"], "status": "indexed", "bytes": byte_count, **result})
            print(f"[OK] {item['key']}: {result['chunks']} chunks ({byte_count} bytes)")
        except Exception as exc:
            results.append({"key": item["key"], "status": "failed", "error": str(exc)})
            print(f"[FAIL] {item['key']}: {exc}")
    print(json.dumps(results, indent=2))
    return 1 if any(x["status"] == "failed" for x in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
