"""
chatbot.py
----------
Intent parser + response engine for the WikiNews chatbot.
Handles greetings, topic queries, follow-ups, and unknowns.
Combines Wikipedia, Reddit, and web search for best answers.
"""
from wiki_engine import search_topics, fetch_page, summarise, extract_keywords
from reddit_engine import search_reddit, get_reddit_summary
from search_engine import search_web, get_web_summary
import re

# ─────────────────────────────────────────────
# Intent patterns
# ─────────────────────────────────────────────

GREET_PATTERNS = re.compile(
    r"\b(hi|hello|hey|howdy|sup|what'?s up|good morning|good evening|greetings)\b", re.I
)
THANKS_PATTERNS = re.compile(r"\b(thanks|thank you|thx|ty|cheers|great|awesome|perfect)\b", re.I)
BYE_PATTERNS    = re.compile(r"\b(bye|goodbye|exit|quit|stop|close|see you|cya)\b", re.I)
HELP_PATTERNS   = re.compile(r"\b(help|what can you do|commands|how does this work|features)\b", re.I)
MORE_PATTERNS    = re.compile(r"\b(more|tell me more|expand|elaborate|details|full article|continue)\b", re.I)
KEYWORD_PATTERNS = re.compile(r"\b(keywords?|key points?|topics?|tags?)\b", re.I)
# NOTE: SUMMARY_PATTERNS removed — the main topic-search branch already handles all summary requests

GREET_REPLIES = [
    "Hey there! 👋 Ask me about any topic — I'll pull the latest summary from Wikipedia.",
    "Hello! I'm WikiBot. What topic would you like to explore today?",
    "Hi! I can fetch and summarise Wikipedia articles for you. What are you curious about?",
]

HELP_TEXT = """
Here's what I can do:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 Ask about any topic       → Combines Wikipedia + Reddit + Web
📰 Get the best answer       → I compare all sources for you
🔑 Extract keywords          → "Keywords for quantum computing"
📖 Read more                 → "Tell me more" (after a result)
👋 Greeting / smalltalk      → supported!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Just type naturally — I'll fetch from Wikipedia, Reddit & web!
"""


# ─────────────────────────────────────────────
# Session state (per-user memory)
# ─────────────────────────────────────────────

class Session:
    def __init__(self):
        self.last_title: str | None = None
        self.last_text: str | None = None
        self.last_url: str | None = None
        self.last_reddit: list = []
        self.last_web: list = []
        self.history: list[dict] = []
        self._greet_idx = 0

    def greet(self) -> str:
        msg = GREET_REPLIES[self._greet_idx % len(GREET_REPLIES)]
        self._greet_idx += 1
        return msg

    def remember(self, title: str, text: str, reddit_results: list = None, web_results: list = None, url: str = None):
        self.last_title = title
        self.last_text = text
        self.last_url = url
        self.last_reddit = reddit_results or []
        self.last_web = web_results or []

    def add(self, role: str, text: str):
        self.history.append({"role": role, "text": text})


# ─────────────────────────────────────────────
# Core response logic
# ─────────────────────────────────────────────

def _merge_sources(wiki_summary: str, topic: str) -> tuple[str, list, list]:
    """
    Fetch Reddit and web results, merge with Wikipedia into best answer.
    Returns (combined_text, reddit_results, web_results).
    """
    reddit_results = search_reddit(topic, limit=5)
    web_results = search_web(topic, max_results=5)

    reddit_summary = get_reddit_summary(topic, max_posts=3)
    web_summary = get_web_summary(topic, max_results=3)

    parts = [wiki_summary]
    if reddit_summary:
        parts.append(f" **Reddit discussions:** {reddit_summary}")
    if web_summary:
        parts.append(f" **From the web:** {web_summary}")

    combined = "".join(parts).strip()
    return combined, reddit_results, web_results


def _extract_topic(message: str) -> str:
    """Strip filler phrases to isolate the search topic."""
    fillers = [
        r"^(tell me about|what('?s| is) happening with|news about|latest on|"
        r"search for|find|explain|summarise|about|i want to know about|"
        r"can you explain|what do you know about)\s+",
    ]
    topic = message.strip()
    for pattern in fillers:
        topic = re.sub(pattern, "", topic, flags=re.I).strip()
    return topic or message


def respond(message: str, session: Session) -> dict:
    """
    Process a user message and return a response dict:
      {
        "text": str,
        "title": str | None,
        "url": str | None,
        "keywords": list | None,
        "results": list | None,   # disambiguation choices
        "type": "info"|"error"|"greeting"|"bye"
      }
    """
    msg = message.strip()
    session.add("user", msg)

    # ── Goodbye ──
    if BYE_PATTERNS.search(msg):
        reply = "Goodbye! Come back whenever you're curious. 👋"
        session.add("bot", reply)
        return {"text": reply, "type": "bye"}

    # ── Greeting ──
    if GREET_PATTERNS.search(msg) and len(msg.split()) <= 5:
        reply = session.greet()
        session.add("bot", reply)
        return {"text": reply, "type": "greeting"}

    # ── Thanks ──
    if THANKS_PATTERNS.search(msg) and len(msg.split()) <= 6:
        reply = "Happy to help! Ask me about another topic anytime. 😊"
        session.add("bot", reply)
        return {"text": reply, "type": "greeting"}

    # ── Help ──
    if HELP_PATTERNS.search(msg):
        session.add("bot", HELP_TEXT)
        return {"text": HELP_TEXT, "type": "help"}

    # ── More / expand ──
    if MORE_PATTERNS.search(msg) and len(msg.split()) <= 5:
        if session.last_text and session.last_title:
            longer = summarise(session.last_text, n_sentences=10)
            reddit_sum = get_reddit_summary(session.last_title, max_posts=2) if session.last_title else ""
            if reddit_sum:
                longer += f" **Reddit:** {reddit_sum}"
            reply = longer
            session.add("bot", reply)
            kws = extract_keywords(session.last_text) if session.last_text else None
            return {
                "text": reply,
                "title": session.last_title,
                "url": session.last_url,
                "keywords": kws,
                "reddit": session.last_reddit,
                "web": session.last_web,
                "type": "info",
            }
        else:
            reply = "There's nothing to expand — ask me about a topic first."
            session.add("bot", reply)
            return {"text": reply, "type": "error"}

    # ── Keywords only ──
    if KEYWORD_PATTERNS.search(msg):
        # Remove the keyword trigger words to see if user provided an explicit topic
        cleaned = re.sub(KEYWORD_PATTERNS, "", msg).strip()
        topic = _extract_topic(cleaned) if cleaned else None

        # If user provided a topic, fetch that page and return keywords
        if topic:
            results = search_topics(topic, limit=5)
            if not results:
                reply = f"I couldn't find anything for **{topic}** to extract keywords from."
                session.add("bot", reply)
                return {"text": reply, "type": "error"}

            best = results[0]
            page = fetch_page(best["title"])
            if not page or not page.get("text"):
                reply = f"Found a page for **{best['title']}** but couldn't extract its content."
                session.add("bot", reply)
                return {"text": reply, "type": "error"}

            keywords = extract_keywords(page["text"]) or []
            session.remember(page.get("title"), page.get("text"), reddit_results=[], web_results=[], url=page.get("url"))
            reply = f"Keywords for **{page.get('title')}**: {', '.join(keywords)}" if keywords else f"No clear keywords found for **{page.get('title')}**."
            session.add("bot", reply)
            return {
                "text": reply,
                "title": page.get("title"),
                "url": page.get("url"),
                "keywords": keywords,
                "type": "info",
            }

        # No explicit topic: fall back to last topic in session
        if session.last_text:
            keywords = extract_keywords(session.last_text) or []
            reply = f"Keywords from the last topic ({session.last_title}): {', '.join(keywords)}" if keywords else "Couldn't extract clear keywords from the last topic."
            session.add("bot", reply)
            return {
                "text": reply,
                "title": session.last_title,
                "keywords": keywords,
                "type": "info",
            }

        # Nothing to extract from
        reply = "Tell me which topic you'd like keywords for, or ask about something first."
        session.add("bot", reply)
        return {"text": reply, "type": "error"}

    # ── Main topic search ──
    topic = _extract_topic(msg)
    if len(topic) < 2:
        reply = "Could you give me a bit more to go on? Try asking about a topic like 'climate change' or 'space exploration'."
        session.add("bot", reply)
        return {"text": reply, "type": "error"}

    # Search Wikipedia
    results = search_topics(topic, limit=5)
    if not results:
        reply = f"I couldn't find anything on **{topic}**. Try rephrasing or check your spelling."
        session.add("bot", reply)
        return {"text": reply, "type": "error"}

    # Fetch the top result
    best = results[0]
    page = fetch_page(best["title"])

    if not page or not page.get("text"):
        reply = f"Found a page for **{best['title']}** but couldn't extract its content. Try another query."
        session.add("bot", reply)
        return {"text": reply, "type": "error"}

    wiki_summary = summarise(page["text"], n_sentences=5)
    # Merge with Reddit + Web for best answer
    reply, reddit_results, web_results = _merge_sources(wiki_summary, topic)

    keywords = extract_keywords(page["text"])
    session.remember(
        page.get("title"),
        page.get("text"),
        reddit_results=reddit_results,
        web_results=web_results,
        url=page.get("url"),
    )

    session.add("bot", reply)

    return {
        "text": reply,
        "title": page.get("title"),
        "url": page.get("url"),
        "keywords": keywords,
        "results": results[1:],
        "reddit": reddit_results,
        "web": web_results,
        "type": "info",
    }
