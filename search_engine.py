"""
search_engine.py
---------------
Web search via DuckDuckGo (Google-like results, no API key required).
"""


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web via DuckDuckGo.
    Returns list of dicts: {title, url, snippet}
    """
    try:
        from duckduckgo_search import DDGS

        ddgs = DDGS()
        results = list(ddgs.text(query, max_results=max_results))
        return [
            {
                "title": r.get("title", "")[:150],
                "url": r.get("href", ""),
                "snippet": (r.get("body", "") or "")[:350],
            }
            for r in results if r.get("title")
        ]
    except Exception:
        return []


def get_web_summary(query: str, max_results: int = 3) -> str:
    """
    Get a condensed summary from web search results.
    """
    results = search_web(query, max_results=max_results)
    if not results:
        return ""

    parts = [r.get("snippet", "") for r in results if r.get("snippet")]
    return " ".join(parts)[:600] if parts else ""
