import pytest
import requests

from scripts import refresh_indian_legal_corpus as ingest


class FakeResponse:
    def __init__(self, status=200, body=b"", content_type="text/html"):
        self.status_code = status
        self.headers = {"Content-Type": content_type}
        self.body = body
        self.closed = False

    def iter_content(self, chunk_size):
        yield self.body

    def close(self):
        self.closed = True


def _long_html():
    text = "Official statutory text and legal provisions. " * 30
    return ("<html><body><h1>Official source</h1><p>" + text + "</p></body></html>").encode()


def test_rejects_non_allowlisted_url_before_http_request():
    calls = []
    with pytest.raises(ingest.DocumentFetchError) as error:
        ingest.extract_document(
            {"key": "bad", "url": "https://example.com/law.pdf", "format": "pdf"},
            request_get=lambda *a, **k: calls.append((a, k)),
        )
    assert calls == []
    assert error.value.diagnostics["stage"] == "url_validation"


def test_reports_http_status_without_claiming_download_failure():
    response = FakeResponse(status=403)
    with pytest.raises(ingest.DocumentFetchError) as error:
        ingest.extract_document(
            {"key": "bns", "url": "https://www.indiacode.nic.in/law.pdf", "format": "pdf"},
            request_get=lambda *a, **k: response,
        )
    assert error.value.diagnostics["stage"] == "http_response"
    assert error.value.diagnostics["http_status"] == 403
    assert response.closed


def test_reports_network_exception_stage_and_type(monkeypatch):
    monkeypatch.setattr(ingest, "MAX_ATTEMPTS", 1)
    monkeypatch.setattr(ingest.time, "sleep", lambda *_: None)

    def fail(*args, **kwargs):
        raise requests.Timeout("read timed out")

    with pytest.raises(ingest.DocumentFetchError) as error:
        ingest.extract_document(
            {"key": "bns", "url": "https://www.indiacode.nic.in/law.pdf", "format": "pdf"},
            request_get=fail,
        )
    assert error.value.diagnostics["stage"] == "http_request"
    failure = error.value.diagnostics["failures"][0]
    assert failure["attempts"][0]["exception_type"] == "Timeout"


def test_detects_html_error_page_returned_for_pdf():
    response = FakeResponse(body=b"<html><body>Access denied</body></html>")
    with pytest.raises(ingest.DocumentFetchError) as error:
        ingest.extract_document(
            {"key": "bns", "url": "https://www.indiacode.nic.in/law.pdf", "format": "pdf"},
            request_get=lambda *a, **k: response,
        )
    assert error.value.diagnostics["stage"] == "extraction"
    assert "expected_pdf_received_html" in error.value.diagnostics["failures"][0]["attempts"][0]["error"]


def test_configured_official_fallback_is_used_and_reported():
    primary_responses = [FakeResponse(status=503) for _ in range(ingest.MAX_ATTEMPTS)]
    fallback = FakeResponse(body=_long_html())
    calls = []

    def get(url, **kwargs):
        calls.append(url)
        return primary_responses.pop(0) if primary_responses else fallback

    text, raw, diagnostics = ingest.extract_document(
        {
            "key": "test-law",
            "url": "https://www.indiacode.nic.in/primary.html",
            "fallback_urls": ["https://www.mha.gov.in/fallback.html"],
            "format": "html",
        },
        request_get=get,
    )
    assert len(text) >= ingest.MIN_TEXT_CHARS
    assert raw == fallback.body
    assert diagnostics["source_role"] == "configured_official_fallback"
    assert diagnostics["fallbacks_configured"] == 1
    assert diagnostics["fallbacks_attempted"] == 1
    assert calls == [
        "https://www.indiacode.nic.in/primary.html",
        "https://www.indiacode.nic.in/primary.html",
        "https://www.indiacode.nic.in/primary.html",
        "https://www.mha.gov.in/fallback.html",
    ]


def test_does_not_claim_fallback_when_none_is_configured():
    with pytest.raises(ingest.DocumentFetchError) as error:
        ingest.extract_document(
            {"key": "bns", "url": "https://www.indiacode.nic.in/law.pdf", "format": "pdf"},
            request_get=lambda *a, **k: FakeResponse(status=404),
        )
    assert error.value.diagnostics["fallbacks_configured"] == 0
    assert error.value.diagnostics["fallbacks_attempted"] == 0
