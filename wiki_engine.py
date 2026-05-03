"""
wiki_engine.py
--------------
Handles all Wikipedia API calls and NLP summarisation.
Uses Python's built-in libraries + requests.
"""

import re
import math
import requests
from collections import Counter

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "WikiNewsChatbot/1.0 (college project)"}

# ─────────────────────────────────────────────
# 1. SEARCH
# ─────────────────────────────────────────────

def search_topics(query: str, limit: int = 5) -> list[dict]:
    """Return a list of matching Wikipedia page titles + snippets."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": limit,
        "format": "json",
    }
    try:
        r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=8)
        data = r.json()
        results = data.get("query", {}).get("search", [])
        return [
            {
                "title": item["title"],
                "snippet": _clean_html(item.get("snippet", "")),
            }
            for item in results
        ]
    except Exception:
        return []


# ─────────────────────────────────────────────
# 2. FETCH PAGE CONTENT
# ─────────────────────────────────────────────

def fetch_page(title: str) -> dict | None:
    """Fetch the full intro/summary section of a Wikipedia article."""
    params = {
        "action": "query",
        "prop": "extracts|info|categories",
        "exintro": 1,             # intro section only — use 1, not True (avoids "True" string serialisation)
        "explaintext": 1,         # plain text, no HTML
        "exchars": 5000,          # cap at 5000 chars to avoid silent server-side truncation
        "inprop": "url",
        "titles": title,
        "format": "json",
        "redirects": 1,
    }
    try:
        r = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=8)
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values()))

        if "missing" in page:
            return None

        return {
            "title": page.get("title", title),
            "url": page.get("fullurl", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"),
            "text": page.get("extract", ""),
        }
    except Exception:
        return None


# ─────────────────────────────────────────────
# 3. NLP SUMMARISATION  (TextRank-lite)
# ─────────────────────────────────────────────

STOPWORDS = {
    "a","an","the","is","it","in","on","at","to","for","of","and","or","but",
    "was","were","are","be","been","being","have","has","had","do","does","did",
    "will","would","could","should","may","might","shall","that","this","these",
    "those","with","from","by","as","its","their","they","he","she","we","you",
    "i","me","my","our","your","his","her","also","which","who","what","when",
    "where","how","not","no","so","if","then","than","there","about","up","out",
    "into","over","after","such","between","each","more","other","some","said",
}

def _clean_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)

def _tokenise(text: str) -> list[str]:
    return re.findall(r"\b[a-zA-Z]+\b", text.lower())

def _sentence_score(sentence: str, word_freq: Counter) -> float:
    words = _tokenise(sentence)
    if not words:
        return 0.0
    score = sum(word_freq.get(w, 0) for w in words if w not in STOPWORDS)
    # normalise by sentence length to avoid bias toward long sentences
    return score / math.log(len(words) + 1)

def summarise(text: str, n_sentences: int = 5) -> str:
    """Extract the top N most informative sentences from text."""
    if not text:
        return "No content available."

    # Split into sentences
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s for s in sentences if len(s.split()) > 5]  # skip tiny fragments

    if not sentences:
        return text[:500]

    # Word frequency (excluding stopwords)
    all_words = [w for w in _tokenise(text) if w not in STOPWORDS]
    word_freq = Counter(all_words)

    # Score each sentence
    scored = [(s, _sentence_score(s, word_freq)) for s in sentences]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Pick top N, then restore original order for readability
    top_set = set(s for s, _ in scored[:n_sentences])
    ordered = [s for s in sentences if s in top_set]

    return " ".join(ordered)


# ─────────────────────────────────────────────
# 4. KEYWORD EXTRACTOR
# ─────────────────────────────────────────────

def extract_keywords(text: str, top_n: int = 6) -> list[str]:
    """Pull the most significant keywords from a block of text."""
    words = [w for w in _tokenise(text) if w not in STOPWORDS and len(w) > 3]
    freq = Counter(words)
    return [word for word, _ in freq.most_common(top_n)]
