"""Retired installer.

The legacy server-side chat-history patch targeted an older repository layout,
overwrote ``send()`` in ``app.js`` without the 30-message / 14,000-character
request bounds, and exposed all conversations to every visitor (no login).
ARLAW AI Global 3.0.3 ships browser-local chat history in ``app/static/app.js``.
"""
raise SystemExit(
    "install_chat_history.py is retired: chat history is built in (browser-local). "
    "Running the old patch would remove the request-size safeguards."
)
