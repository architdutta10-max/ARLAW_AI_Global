
import app.llm as llm


class FakeResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code
        self.ok = status_code < 400
        self.text = ""

    def json(self):
        return self.data


def test_system_prompt_contains_safety_rules():
    messages = llm._messages([{
        "role": "user",
        "content": "Explain a legal question."
    }])

    assert messages[0]["role"] == "system"
    assert "Never invent" in messages[0]["content"]


def test_retrieved_context_is_separate():
    messages = llm._messages(
        [{"role": "user", "content": "Question"}],
        "[S1] Example source"
    )

    assert any(
        "Example source" in item["content"]
        for item in messages
    )


def test_message_history_is_limited():
    history = [
        {"role": "user", "content": str(i)}
        for i in range(20)
    ]

    result = llm._messages(history)

    assert len(result) == 15


def test_groq_uses_completion_token_parameter(monkeypatch):
    captured = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured["json"] = kwargs["json"]

        return FakeResponse({
            "choices": [{
                "message": {"content": "Test answer"}
            }]
        })

    monkeypatch.setattr(llm.requests, "post", fake_post)
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    answer = llm._groq([
        {"role": "user", "content": "Test"}
    ])

    assert answer == "Test answer"
    assert "max_completion_tokens" in captured["json"]
    assert "max_tokens" not in captured["json"]


def test_provider_selection_rejects_unknown(monkeypatch):
    monkeypatch.setenv("ARLAW_AI_PROVIDER", "unknown")

    answer, error = llm.generate([
        {"role": "user", "content": "Test"}
    ])

    assert answer is None
    assert "Unsupported AI provider" in error


def test_auto_falls_back_to_ollama(monkeypatch):
    monkeypatch.setenv("ARLAW_AI_PROVIDER", "auto")
    monkeypatch.setenv("GROQ_API_KEY", "")

    monkeypatch.setattr(
        llm,
        "_ollama",
        lambda messages: "Local answer"
    )

    answer, error = llm.generate([
        {"role": "user", "content": "Test"}
    ])

    assert answer == "Local answer"
    assert error is None
