# Setup Guide (Free / No Keys)

This project runs fully in mock mode without any API keys. Use this guide to keep the demo free and easy to configure.

## 1) Prerequisites
- Node.js 18+
- Python 3.9+
- npm

## 2) Install Dependencies

```bash
# Backend
cd backend && npm install

# Frontend
cd frontend && npm install

# AI layer (recommended: Python 3.11)
cd ai
/opt/homebrew/bin/python3.11 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

## 3) Run in Free Mode (Mock)
Mock mode is already the default. It does not call any external LLM.

```bash
# From repo root
npm run dev
```

If the AI server startup stalls on ChromaDB/numpy imports, run:

```bash
DISABLE_CHROMA=true npm run dev
```

Live audio mode works without keys by using browser speech recognition
(Chrome recommended) and still streams audio to the backend.
When prompted, allow microphone access.

Open http://localhost:3000

## 4) Optional: Use a Paid/Trial Key (If Available)
If you have a trial or paid OpenAI key, you can enable live mode. This is optional and not required for the demo.

```bash
# Create .env (if not already)
cp .env.example .env
```

Edit `.env` and set:

```
MOCK_MODE=false
OPENAI_API_KEY=your_key_here
```

## 5) Troubleshooting
- If you see no stream, verify the backend is running on port 3001.
- If the UI is blank, confirm Next.js is running on port 3000.
- If AI outputs are empty, ensure the AI server is running on port 8000.

## 6) Verify AI Pipeline (Free)

```bash
cd ai && MOCK_MODE=true pytest tests/ -v
```

This keeps the demo free and reproducible.
