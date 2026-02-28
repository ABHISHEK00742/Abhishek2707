"""
reddit_engine.py
---------------
Search Reddit for posts and discussions related to a topic.
Uses Reddit's public JSON API (no OAuth required for read-only).
"""

import re
import requests

REDDIT_BASE = "https://www.reddit.com"
HEADERS = {"User-Agent": "WikiNewsChatbot/1.0 (multi-source search; educational)"}


def _clean_text(text: str) -> str:
    """Remove markdown and excess whitespace."""
    if not text:
        return ""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # [link](url) -> link
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)       # **bold** -> bold
    text = re.sub(r"\s+", " ", text).strip()
    return text[:500]  # Cap length


def search_reddit(query: str, limit: int = 5) -> list[dict]:
    """
    Search Reddit for posts matching the query.
    Returns list of dicts: {title, subreddit, url, snippet, score}
    """
    try:
        url = f"{REDDIT_BASE}/search.json"
        params = {"q": query, "limit": min(limit, 10), "sort": "relevance"}
        r = requests.get(url, params=params, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return []

        data = r.json()
        children = data.get("data", {}).get("children", [])

        results = []
        for child in children:
            post = child.get("data", {})
            title = post.get("title", "")
            subreddit = post.get("subreddit", "")
            selftext = post.get("selftext", "") or ""
            score = post.get("score", 0)
            permalink = post.get("permalink", "")
            url = f"{REDDIT_BASE}{permalink}" if permalink else ""

            # Use selftext as snippet if available, else title
            snippet = _clean_text(selftext) if selftext else _clean_text(title)
            if not snippet:
                continue

            results.append({
                "title": title[:200],
                "subreddit": subreddit,
                "url": url,
                "snippet": snippet[:400],
                "score": score,
            })
        return results[:limit]
    except Exception:
        return []


def get_reddit_summary(query: str, max_posts: int = 3) -> str:
    """
    Get a condensed summary from Reddit for the topic.
    Combines top post snippets into a readable block.
    """
    posts = search_reddit(query, limit=max_posts)
    if not posts:
        return ""

    parts = []
    for i, p in enumerate(posts, 1):
        sub = p.get("subreddit", "")
        snippet = p.get("snippet", "")
        if snippet:
            parts.append(f"From r/{sub}: {snippet}")
    return " ".join(parts)[:800] if parts else ""
