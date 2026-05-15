# AI Co-Pilot de Streaming Contextual

A real-time AI system that analyzes a continuous text stream and generates summaries, questions, and insights using a multi-agent pipeline with RAG (Retrieval-Augmented Generation).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                  │
│   ┌──────────┐  ┌──────────────┐  ┌─────────────────┐  │
│   │ Summary  │  │  Questions   │  │    Insights     │  │
│   │  Panel   │  │    Panel     │  │     Panel       │  │
│   └──────────┘  └──────────────┘  └─────────────────┘  │
│   ┌───────────────────┐        ┌───────────────────┐  │
│   │ Key Moments Panel │        │ Action Agent Panel│  │
│   └───────────────────┘        └───────────────────┘  │
│              WebSocket (ws://localhost:3001)             │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              BACKEND (Node.js + Express + WS)           │
│   ┌──────────────────┐    ┌──────────────────────────┐  │
│   │  Stream Emitter  │    │      WebSocket Server    │  │
│   │  (chunks/2s)     │───▶│   (broadcasts to all)   │  │
│   └──────────────────┘    └────────────┬─────────────┘  │
└────────────────────────────────────────│────────────────┘
                                         │ HTTP POST /process
┌────────────────────────────────────────▼────────────────┐
│                AI LAYER (Python FastAPI)                 │
│   ┌──────────┐  ┌──────────────┐  ┌─────────────────┐  │
│   │Summarizer│  │  Question    │  │    Insight      │  │
│   │  Agent   │  │  Generator   │  │   Generator     │  │
│   └────┬─────┘  └──────┬───────┘  └────────┬────────┘  │
│        └───────────────┴──────────────────┘            │
│   ┌──────────┐  ┌──────────────┐                        │
│   │ Alert    │  │   Action     │                        │
│   │ Agent    │  │   Agent      │                        │
│   └──────────┘  └──────────────┘                        │
│                    ┌──────────┐                         │
│                    │ ChromaDB │ (RAG / vector store)    │
│                    └──────────┘                         │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer    | Technology                                    |
|----------|-----------------------------------------------|
| Frontend | Next.js 14 (App Router), TypeScript, CSS      |
| Backend  | Node.js, Express, ws (WebSockets), Axios      |
| AI Layer | Python, FastAPI, LangChain, ChromaDB, OpenAI  |
| Testing  | Jest (Node.js), pytest (Python)               |

## Project Structure

```
/
├── backend/                 # Node.js WebSocket server + stream emitter
│   ├── src/
│   │   ├── index.js         # Main entry (HTTP + WS server)
│   │   ├── streamer.js      # Text stream emitter (chunks every 2s)
│   │   └── wsServer.js      # WebSocket server + AI HTTP client
│   └── tests/               # Jest tests
├── ai/                      # Python AI layer
│   ├── agents/              # Summarizer, QuestionGenerator, InsightGenerator
│   ├── rag/                 # ChromaDB RAG engine
│   ├── orchestrator.py      # Pipeline coordinator
│   ├── server.py            # FastAPI server
│   └── tests/               # pytest tests
├── frontend/                # Next.js frontend
│   └── src/app/
│       ├── page.tsx         # Main page with real-time panels + key moments
│       ├── layout.tsx       # Root layout
│       └── globals.css      # Styles
└── package.json             # Root scripts (concurrently)
```

## Setup

### Prerequisites
- Node.js 18+
- Python 3.9+
- npm

### Install Dependencies

```bash
# Backend
cd backend && npm install

# Frontend
cd frontend && npm install

# AI Layer
cd ai && pip install -r requirements.txt
```

## Running

### Run All Services Together
```bash
npm install   # install concurrently
npm run dev   # starts all 3 services
```

### Run Services Individually
```bash
# Terminal 1 — AI server (port 8000)
npm run dev:ai

# Terminal 2 — Backend (port 3001)
npm run dev:backend

# Terminal 3 — Frontend (port 3000)
npm run dev:frontend
```

Then open http://localhost:3000 in your browser.

## Running Tests

```bash
# All tests
npm test

# Backend tests only (Jest)
npm run test:backend

# AI tests only (pytest)
npm run test:ai
```

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

| Variable              | Default                    | Description                         |
|-----------------------|----------------------------|-------------------------------------|
| `PORT`                | `3001`                     | Backend port                        |
| `AI_URL`              | `http://localhost:8000`    | Python AI server URL                |
| `STREAM_INTERVAL`     | `2000`                     | Milliseconds between stream chunks  |
| `OPENAI_API_KEY`      | `your_key_here`            | OpenAI API key (optional)           |
| `MOCK_MODE`           | `true`                     | Use mock responses (no API key needed) |
| `NEXT_PUBLIC_WS_URL`  | `ws://localhost:3001`      | WebSocket URL for the frontend      |

## Mock Mode

By default (`MOCK_MODE=true`), the system runs without an OpenAI API key. All agents return intelligent pre-programmed responses based on content keywords. Set `MOCK_MODE=false` and provide `OPENAI_API_KEY` to use real LLM responses.

## Demo Flow

1. Frontend connects via WebSocket to the backend
2. Backend auto-starts streaming educational text about AI (12 sentences, 2s apart)
3. Each chunk is broadcast to all WebSocket clients
4. Backend calls the Python AI server for each chunk
5. AI pipeline: chunk → ChromaDB (store) → RAG retrieval → 5 agents → response
6. AI results are broadcast to all WebSocket clients
7. Frontend updates panels in real-time: Summary, Questions, Insights, Key Moments, Action Agent
