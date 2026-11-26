"""Explicitly refresh ARLAW's India primary-law corpus from allowlisted official URLs.

Run: python scripts/refresh_indian_legal_corpus.py [--keys bns_2023]
This command is opt-in; it never runs during web-service startup. It records
actual HTTP/download/extraction/indexing outcomes and preserves the last good
indexed copy unless a replacement has been downloaded and extracted successfully.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "app" / "indian_legal_sources.json"
ALLOWED_HOSTS = {
    "www.indiacode.nic.in", "indiacode.nic.in",
    "www.meity.gov.in", "meity.gov.in",
    "www.incometax.gov.in", "www.mha.gov.in", "mha.gov.in",
    "cdnbbsr.s3waas.gov.in", "ldo.mohua.gov.in",
}
MAX_BYTES = 45 * 1024 * 1024
MIN_TEXT_CHARS = 500
MAX_ATTEMPTS = 3
TIMEOUT = (15, 90)
RETRYABLE_STATUS = {429, 500, 502, 503, 504}


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


class DocumentFetchError(RuntimeError):
    def __init__(self, message, diagnostics):
        super().__init__(message)
        self.diagnostics = diagnostics


def _validate_url(url: str) -> str:
    try:
        parsed = urlparse(url)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_url") from exc
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("blocked_non_allowlisted_source")
    if parsed.username or parsed.password:
        raise ValueError("credentials_in_source_url_not_allowed")
    return url


def _extract_payload(item, raw: bytes, content_type: str) -> str:
    fmt = str(item.get("format", "")).lower()
    if not raw:
        raise ValueError("empty_response_body")
    if fmt == "pdf":
        if b"%PDF-" not in raw[:1024]:
            if b"<html" in raw[:4096].lower() or "html" in content_type.lower():
                raise ValueError("expected_pdf_received_html")
            raise ValueError("response_does_not_have_pdf_signature")
        reader = PdfReader(BytesIO(raw), strict=True)
        if reader.is_encrypted:
            raise ValueError("password_protected_pdf")
        max_pages = int(item.get("max_pages", 1500))
        if len(reader.pages) > max_pages:
            raise ValueError(f"pdf_page_limit_exceeded:{len(reader.pages)}>{max_pages}")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif fmt in {"html", "htm"}:
        if raw[:4096].count(b"\x00") > 0:
            raise ValueError("unexpected_binary_html_response")
        parser = TextExtractor()
        parser.feed(raw.decode("utf-8", errors="replace"))
        parser.close()
        text = "\n".join(parser.parts)
    else:
        raise ValueError(f"unsupported_document_format:{fmt or 'missing'}")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if len(text) < MIN_TEXT_CHARS:
        raise ValueError(f"extracted_text_too_short:{len(text)}_characters")
    return text


def _request_one(url: str, item: dict, request_get):
    """Return (text, bytes, attempt diagnostics); never mutate the knowledge DB."""
    try:
        _validate_url(url)
    except ValueError as exc:
        raise DocumentFetchError(str(exc), {
            "stage": "url_validation", "http_status": None, "attempts": []
        }) from exc
    attempts = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = None
        stage = "http_request"
        try:
            response = request_get(
                url,
                timeout=TIMEOUT,
                headers={"User-Agent": "ARLAW-AI-legal-corpus-refresh/3.3.0"},
                stream=True,
                allow_redirects=False,
            )
            status = getattr(response, "status_code", None)
            attempt_info = {"attempt": attempt, "http_status": status, "stage": "http_response"}
            if status in RETRYABLE_STATUS and attempt < MAX_ATTEMPTS:
                attempt_info.update({"outcome": "retryable_http_status"})
                attempts.append(attempt_info)
                time.sleep(0.25 * (2 ** (attempt - 1)))
                continue
            if status is None:
                raise RuntimeError("response_missing_http_status")
            if status < 200 or status >= 300:
                attempt_info.update({"outcome": "http_error"})
                attempts.append(attempt_info)
                raise DocumentFetchError(f"http_status:{status}", {
                    "stage": "http_response", "http_status": status, "attempts": attempts
                })

            stage = "download"
            chunks, total = [], 0
            for block in response.iter_content(chunk_size=256 * 1024):
                if not block:
                    continue
                total += len(block)
                if total > MAX_BYTES:
                    raise ValueError(f"document_exceeds_byte_limit:{MAX_BYTES}")
                chunks.append(block)
            raw = b"".join(chunks)
            content_type = str(getattr(response, "headers", {}).get("Content-Type", ""))
            attempt_info.update({"bytes_downloaded": len(raw), "content_type": content_type})

            stage = "extraction"
            text = _extract_payload(item, raw, content_type)
            attempt_info.update({"outcome": "success", "extracted_characters": len(text)})
            attempts.append(attempt_info)
            return text, raw, {"stage": "complete", "http_status": status, "attempts": attempts}
        except DocumentFetchError:
            raise
        except requests.RequestException as exc:
            info = {"attempt": attempt, "stage": stage, "exception_type": type(exc).__name__,
                    "error": str(exc)[:500]}
            attempts.append(info)
            if attempt < MAX_ATTEMPTS:
                time.sleep(0.25 * (2 ** (attempt - 1)))
                continue
            raise DocumentFetchError("network_request_failed", {
                "stage": stage, "http_status": None, "attempts": attempts
            }) from exc
        except Exception as exc:
            info = {"attempt": attempt, "stage": stage, "exception_type": type(exc).__name__,
                    "error": str(exc)[:500]}
            attempts.append(info)
            raise DocumentFetchError("document_processing_failed", {
                "stage": stage, "http_status": getattr(response, "status_code", None),
                "attempts": attempts
            }) from exc
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass
    raise DocumentFetchError("retry_exhausted", {"stage": "http_request", "attempts": attempts})


def extract_document(item, request_get=None):
    """Try the primary URL and only explicitly configured official fallback URLs."""
    request_get = request_get or requests.get
    urls = [item["url"], *item.get("fallback_urls", [])]
    all_attempts = []
    failures = []
    for index, url in enumerate(urls):
        source_role = "primary" if index == 0 else "configured_official_fallback"
        try:
            text, raw, diag = _request_one(url, item, request_get)
            diag.update({
                "source_role": source_role,
                "source_url": url,
                "fallbacks_configured": max(0, len(urls) - 1),
                "fallbacks_attempted": index,
            })
            diag["attempts"] = all_attempts + diag["attempts"]
            return text, raw, diag
        except DocumentFetchError as exc:
            failures.append({
                "source_role": source_role,
                "source_url": url,
                **exc.diagnostics,
            })
            all_attempts.extend(exc.diagnostics.get("attempts", []))
    diagnostics = {
        "stage": failures[-1].get("stage", "unknown") if failures else "url_validation",
        "http_status": failures[-1].get("http_status") if failures else None,
        "fallbacks_configured": max(0, len(urls) - 1),
        "fallbacks_attempted": max(0, len(failures) - 1),
        "failures": failures,
    }
    raise DocumentFetchError("all_configured_source_urls_failed", diagnostics)


def _record_run(source_url, status, *, raw=None, http_status=None, extracted=0, diagnostics=None):
    """Persist observable facts; do not infer network details not returned by requests."""
    from app.legal_governance import init_governance_db, record_ingestion_run

    init_governance_db()
    return record_ingestion_run(
        source_url=source_url,
        status=status,
        content=raw,
        http_status=http_status,
        extracted_characters=extracted,
        error=json.dumps(diagnostics or {}, ensure_ascii=False)[:2000],
    )


def main():
    parser = argparse.ArgumentParser(description="Refresh selected ARLAW Indian legal sources.")
    parser.add_argument("--keys", nargs="+", help="Only refresh listed source keys.")
    args = parser.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    all_sources = manifest["sources"]
    if args.keys:
        requested = set(args.keys)
        known = {item["key"] for item in all_sources}
        unknown = requested - known
        if unknown:
            parser.error("Unknown source key(s): " + ", ".join(sorted(unknown)))
        selected_sources = [item for item in all_sources if item["key"] in requested]
    else:
        selected_sources = all_sources

    print("Selected sources:", ", ".join(item["key"] for item in selected_sources))
    sys.path.insert(0, str(ROOT))
    from app import knowledge

    knowledge.init_db()
    results = []
    for item in selected_sources:
        managed_name = f"official-refresh:{item['key']}"
        diagnostics, raw, text, indexed_result = {}, None, "", None
        try:
            text, raw, diagnostics = extract_document(item)
            indexed_result = knowledge.add_source(
                title=item["title"], text=text, jurisdiction=item["jurisdiction"],
                source_url=diagnostics["source_url"], as_of=item.get("as_of", ""),
                file_name=managed_name, authority=item.get("authority", "official primary source"),
                language="en", category="law",
            )
            # Replace only after the new copy has been indexed successfully.
            with knowledge.connect() as conn:
                conn.execute(
                    "DELETE FROM chunks WHERE source_id IN "
                    "(SELECT id FROM sources WHERE file_name=? AND id<>?)",
                    (managed_name, indexed_result["id"]),
                )
                conn.execute(
                    "DELETE FROM sources WHERE file_name=? AND id<>?",
                    (managed_name, indexed_result["id"]),
                )
            result_row = {
                "key": item["key"], "status": "indexed", "bytes": len(raw),
                "extracted_characters": len(text), "source_role": diagnostics["source_role"],
                "fallbacks_configured": diagnostics["fallbacks_configured"],
                "fallbacks_attempted": diagnostics["fallbacks_attempted"],
                **indexed_result,
            }
            try:
                _record_run(
                    diagnostics["source_url"], "completed", raw=raw,
                    http_status=diagnostics.get("http_status"),
                    extracted=len(text), diagnostics=diagnostics,
                )
            except Exception as log_exc:
                result_row["diagnostic_persistence_warning"] = (
                    f"{type(log_exc).__name__}: {str(log_exc)[:300]}"
                )
            results.append(result_row)
            print(f"[OK] {item['key']}: {indexed_result['chunks']} chunks; "
                  f"{len(raw)} bytes; {len(text)} extracted characters")
        except Exception as exc:
            if isinstance(exc, DocumentFetchError):
                diagnostics, error_type = exc.diagnostics, type(exc).__name__
            else:
                diagnostics = {
                    "stage": "cleanup" if indexed_result else ("indexing" if text else "unknown"),
                    "exception_type": type(exc).__name__, "error": str(exc)[:500],
                    "fallbacks_configured": len(item.get("fallback_urls", [])),
                }
                error_type = type(exc).__name__
            if indexed_result is None:
                try:
                    _record_run(
                        item["url"], "failed", raw=raw,
                        http_status=diagnostics.get("http_status"),
                        extracted=len(text), diagnostics={"error_type": error_type, **diagnostics},
                    )
                except Exception as log_exc:
                    diagnostics["diagnostic_persistence_error"] = (
                        f"{type(log_exc).__name__}: {str(log_exc)[:300]}"
                    )
                results.append({
                    "key": item["key"], "status": "failed", "error_type": error_type,
                    "diagnostics": diagnostics, "previous_indexed_copy_preserved": True,
                })
                print(f"[FAIL] {item['key']}: {error_type}: "
                      f"{json.dumps(diagnostics, ensure_ascii=False)}")
            else:
                results.append({
                    "key": item["key"], "status": "partial",
                    "new_source_id": indexed_result["id"], "error_type": error_type,
                    "diagnostics": diagnostics, "replacement_indexed": True,
                })
                print(f"[PARTIAL] {item['key']}: replacement indexed, "
                      f"post-index cleanup failed: {json.dumps(diagnostics, ensure_ascii=False)}")

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 1 if any(x["status"] in {"failed", "partial"} for x in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
