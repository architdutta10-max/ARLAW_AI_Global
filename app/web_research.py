"""Shared external research gateway. Uses Tavily when configured; never fabricates results."""
from __future__ import annotations
import os
from datetime import datetime, timezone
import requests

TAVILY_ENDPOINT = "https://api.tavily.com/search"

def web_research_status() -> dict:
    enabled = os.getenv("ARLAW_WEB_RESEARCH_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
    configured = bool(os.getenv("TAVILY_API_KEY", "").strip())
    return {
        "enabled": enabled,
        "provider": "tavily" if enabled and configured else None,
        "configured": configured,
        "available": bool(enabled and configured),
        "limitation": None if enabled and configured else (
            "Web research is disabled by configuration." if not enabled
            else "TAVILY_API_KEY is not configured; no live web search is performed."
        ),
    }

def search_web(query: str, jurisdiction: str = "IN", max_results: int = 5) -> list[dict]:
    status = web_research_status()
    if not status["available"] or not str(query or "").strip():
        return []
    key = os.getenv("TAVILY_API_KEY", "").strip()
    response = requests.post(
        TAVILY_ENDPOINT,
        json={
            "api_key": key,
            "query": str(query)[:2000],
            "search_depth": os.getenv("ARLAW_WEB_SEARCH_DEPTH", "advanced"),
            "max_results": max(1, min(int(max_results), 8)),
            "include_answer": False,
            "include_raw_content": False,
            "topic": "general",
        },
        timeout=(5, 20),
    )
    response.raise_for_status()
    payload = response.json()
    now = datetime.now(timezone.utc).isoformat()
    results = []
    for item in payload.get("results", []):
        url = str(item.get("url") or "").strip()
        title = str(item.get("title") or "").strip()
        content = str(item.get("content") or "").strip()
        if not url.startswith(("https://", "http://")) or not content:
            continue
        results.append({
            "title": title[:500] or url,
            "url": url[:2000],
            "content": content[:5000],
            "score": item.get("score"),
            "published_date": item.get("published_date"),
            "jurisdiction_requested": jurisdiction,
            "retrieved_at": now,
            "source_type": "external_web_search",
        })
    return results
