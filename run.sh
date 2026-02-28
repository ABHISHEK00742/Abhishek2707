#!/bin/bash
# ─────────────────────────────────────────────
#  WikiNews Chatbot — Setup & Run Script
#  Usage:  bash run.sh          → Web UI (http://localhost:5000)
#          bash run.sh cli      → Terminal / CLI version
# ─────────────────────────────────────────────

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/venv"

# ── Step 1: Create virtual environment if it doesn't exist ──
if [ ! -d "$VENV_DIR" ]; then
    echo "📦  Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✅  Virtual environment created at $VENV_DIR"
fi

# ── Step 2: Activate and install dependencies ──
source "$VENV_DIR/bin/activate"

echo "📥  Installing / verifying dependencies..."
pip install -q -r requirements.txt
echo "✅  Dependencies ready"

# ── Step 3: Launch ──
if [ "$1" = "cli" ]; then
    echo ""
    echo "🖥️   Launching CLI version..."
    python cli.py
else
    echo ""
    echo "═══════════════════════════════════════════"
    echo "  🌐  WikiNews Chatbot — Web UI"
    echo "  👉  Open http://localhost:5000"
    echo "  🛑  Press Ctrl+C to stop"
    echo "═══════════════════════════════════════════"
    echo ""
    python app.py
fi
