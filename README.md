# 📰 WikiNews Chatbot

A Python chatbot that fetches and summarises articles from Wikipedia using NLP.
Built for a college project — two modes: **Web UI** (Flask) and **CLI** (terminal).

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Web UI (recommended)
```bash
python app.py
```
Then open **http://localhost:5000** in your browser.

### 3. Run the CLI version
```bash
python cli.py
```

---

## 📁 Project Structure

```
wikinews_chatbot/
├── app.py            ← Flask web server
├── cli.py            ← Terminal chatbot
├── chatbot.py        ← Intent parser + response logic
├── wiki_engine.py    ← Wikipedia API + NLP summariser
├── index.html        ← Web chat UI (served from project root)
├── requirements.txt
└── README.md
```

---

## 💬 How to Use

| What you type              | What happens                        |
|---------------------------|--------------------------------------|
| Tell me about Bitcoin     | Fetches and summarises Wikipedia     |
| What is photosynthesis?   | Same — works naturally               |
| more                      | Gives a longer summary               |
| keywords                  | Extracts key topics from last result |
| help                      | Shows all commands                   |
| quit / exit               | Closes the chatbot                   |

---

## 🧠 How It Works

```
User Input
    ↓
Intent Parser (chatbot.py)
    ↓
Wikipedia API Search (wiki_engine.py)
    ↓
Page Content Fetch
    ↓
NLP Summarisation (TextRank-lite algorithm)
    ↓
Formatted Response → Web UI / CLI
```

### Summarisation Algorithm
Uses a frequency-based TextRank-lite approach:
1. Tokenise text into sentences
2. Count word frequencies (excluding stopwords)
3. Score each sentence by the sum of its word frequencies
4. Normalise by log(sentence_length) to avoid length bias
5. Return the top N highest-scoring sentences in original order

---

## Tech Stack
- Python 3.10+
- requests — Wikipedia API calls
- Flask — Web server
- colorama — CLI colours
- re, collections — Built-in NLP tools

*College Project · WikiNews Chatbot · Built with Python*
