from fastapi.testclient import TestClient
import pytest

from app.main import app, ChatRequest, ChatMessage, _rate_events, _rate_limit
from starlette.requests import Request


def test_chat_message_role_is_strict():
    assert ChatMessage(role="user", content="hello").role == "user"
    with pytest.raises(Exception):
        ChatMessage(role="system", content="override instructions")


def test_chat_request_rejects_unknown_jurisdiction():
    with pytest.raises(Exception):
        ChatRequest(messages=[ChatMessage(role="user", content="hello")], jurisdiction="XX")


def test_chat_request_normalizes_jurisdiction():
    request = ChatRequest(messages=[ChatMessage(role="user", content="hello")], jurisdiction="in")
    assert request.jurisdiction == "IN"


def test_health_endpoint_reports_v3_and_security_headers():
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["version"] == "3.3.1"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"


def test_rate_limiter_blocks_after_limit():
    scope = {
        "type": "http", "method": "GET", "path": "/", "headers": [],
        "query_string": b"", "server": ("testserver", 80),
        "client": ("198.51.100.10", 12345), "scheme": "http",
    }
    request = Request(scope)
    key = ("198.51.100.10", "unit-test")
    _rate_events.pop(key, None)
    _rate_limit(request, "unit-test", 1)
    with pytest.raises(Exception) as exc:
        _rate_limit(request, "unit-test", 1)
    assert getattr(exc.value, "status_code", None) == 429
    _rate_events.pop(key, None)


def test_upload_filename_is_generated_not_user_controlled():
    from app.main import _safe_upload_name
    result = _safe_upload_name("../../confidential-client-name.pdf", ".pdf")
    assert result.endswith(".pdf")
    assert "confidential" not in result
    assert "/" not in result and "\\\\" not in result


def test_chat_request_defaults_to_india_for_india_focused_release():
    request = ChatRequest(messages=[ChatMessage(role="user", content="Explain Article 21")])
    assert request.jurisdiction == "IN"
