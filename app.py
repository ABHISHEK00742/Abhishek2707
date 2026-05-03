"""
app.py
------
Flask web server for the WikiNews Chatbot.
Run with: python app.py
Then open http://localhost:5000 in your browser.
"""

from flask import Flask, request, jsonify, session, send_from_directory
from chatbot import Session, respond
import uuid
import os

# Resolve the directory this file lives in — works regardless of CWD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.secret_key = "wikinews-secret-key-change-in-production"

# In-memory session store  {session_id: Session}
_sessions: dict[str, Session] = {}


def get_session() -> Session:
    """Get or create a chatbot Session for this browser session."""
    sid = session.get("sid")
    if not sid or sid not in _sessions:
        sid = str(uuid.uuid4())
        session["sid"] = sid
        _sessions[sid] = Session()
    return _sessions[sid]


@app.route("/")
def index():
    # Serve index.html from the same directory as this script — works from any CWD.
    return send_from_directory(BASE_DIR, 'index.html')


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = (data or {}).get("message", "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    chat_session = get_session()
    result = respond(message, chat_session)
    return jsonify(result)


@app.route("/reset", methods=["POST"])
def reset():
    sid = session.get("sid")
    if sid and sid in _sessions:
        del _sessions[sid]
    session.clear()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  WikiNews Chatbot is running!")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 50 + "\n")
    app.run(debug=True, port=5000)
