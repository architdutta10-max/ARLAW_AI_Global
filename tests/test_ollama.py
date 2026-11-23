from app import llm


def test_ollama_adapter_uses_native_chat_api(monkeypatch):
    captured = {}

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"message": {"content": "Local model answer"}}

    def fake_post(url, json, timeout):
        captured.update(url=url, payload=json, timeout=timeout)
        return Response()

    monkeypatch.setattr(llm.requests, "post", fake_post)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434/")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
    answer, model, finish = llm._ollama([{"role": "user", "content": "hello"}])
    assert answer == "Local model answer"
    assert model == "qwen3:8b"
    assert finish == "stop"
    assert captured["url"] == "http://localhost:11434/api/chat"
    assert captured["payload"]["stream"] is False


def test_ollama_failure_falls_back_to_groq(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setenv("OLLAMA_ENABLED", "true")
    monkeypatch.setenv("ARLAW_PROVIDER_ORDER", "ollama,groq")
    calls = []

    def local(_payload):
        calls.append("ollama")
        raise RuntimeError("local server unavailable")

    def cloud(_payload):
        calls.append("groq")
        return "Fallback answer", "test-groq-model"

    monkeypatch.setattr(llm, "PROVIDERS", {"ollama": local, "groq": cloud})
    answer, error, meta = llm.generate([{"role": "user", "content": "Explain contract law"}])
    assert error is None
    assert answer == "Fallback answer"
    assert calls == ["ollama", "groq"]
    assert meta["provider"] == "groq"
    assert meta["fallback_used"] is True
