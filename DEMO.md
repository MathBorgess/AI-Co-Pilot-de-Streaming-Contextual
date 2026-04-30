# AI Streaming Copilot — Demo & Learnings

> "This is not a chatbot. It is following what is happening."

---

## 1. Introduction (1 min)

### The Problem
Most AI tools work like search engines: you ask a question, you get an answer.  
But real work doesn't happen in isolated questions — it happens in **continuous, messy streams**: meetings, live calls, incident bridges, strategy sessions.

By the time you finish the meeting and open a chat window, the moment is gone.

### The Trend
Three converging forces make this system timely:
- **Streaming AI** — LLMs can now process incrementally, not in batch
- **Multi-agent systems** — specialized agents outperform one monolithic model
- **RAG (Retrieval-Augmented Generation)** — context gets smarter as it grows

### What This Explores
Can an AI system *attend* a meeting, track decisions, fire alerts on critical moments, and suggest next steps — all **before the meeting ends**?

---

## 2. What Was Built (2 min)

### System Overview

```
Input (text stream, 2 s/chunk)
  ↓
Node.js Backend (WebSocket server)
  ↓ HTTP POST /process per chunk
Python AI Server (FastAPI)
  ↓
  ├─ RAGEngine (ChromaDB) — stores & retrieves context with recency boost
  ├─ SummarizerAgent    — evolving cumulative summary
  ├─ QuestionGenerator  — 2-3 probing questions per chunk
  ├─ InsightGenerator   — pattern-level observations
  ├─ AlertAgent ⚡ NEW  — fires on decisions, risks, conflicts, deadlines
  └─ DirectionAgent �� NEW — suggests concrete next steps
  ↓
WebSocket broadcast → Next.js frontend
  ↓
4-panel real-time UI
  ├─ 🚨 LIVE ALERTS (full-width, animated flash on trigger)
  ├─ 📝 Summary
  ├─ ❓ Questions
  ├─ 💡 Insights
  └─ 🧭 Recommended Actions
```

### Key Ports

| Service  | Technology      | Port |
|----------|-----------------|------|
| Frontend | Next.js 14      | 3000 |
| Backend  | Node.js + WS    | 3001 |
| AI Layer | Python FastAPI  | 8000 |

### What Makes It Different From a Chatbot

| Chatbot | This System |
|---------|-------------|
| You ask, it answers | It listens without being asked |
| Responds to queries | Reacts to *events* in the stream |
| Stateless per session | Builds cumulative context via RAG |
| One model does everything | 5 specialized agents |
| Batch output | Incremental, chunk-by-chunk |

---

## 3. Demonstration (3–4 min)

### Demo Scenario Narrative

> *"Imagine you're in a critical strategy meeting. The company needs to decide whether to build an AI feature in-house or buy a third-party solution. The deadline is next quarter. Legal has concerns. The competitor just shipped. And the team is split."*

### Starting the System

```bash
# Terminal 1 — AI server (port 8000)
cd ai && python server.py

# Terminal 2 — Backend (port 3001)
cd backend && node src/index.js

# Terminal 3 — Frontend (port 3000)
cd frontend && npm run dev
```

Then open **http://localhost:3000**

### What Happens (chunk by chunk)

| Chunk | Content | Alert Fires |
|-------|---------|-------------|
| 1 | "final decision on the AI copilot launch strategy" | ⚠️ Key Decision Point |
| 2 | "deadline is end of next quarter, cannot slip" | 🔥 Time Pressure |
| 3 | "team is split…tension…technical debt" | ⚡ Team Conflict |
| 4 | "architecture may not scale" | — |
| 5 | "buy a third-party AI service" | — |
| 6 | "delay the launch by six weeks" | — |
| 7 | "build, buy, or delay — decide today" | ⚠️ Key Decision Point |
| 8 | "Legal has flagged compliance concerns" | 🛡️ Risk Signal |
| 9 | "competitor launched, gaining traction" | 📊 Competitive Signal |
| 10 | "risk losing three enterprise accounts" | — |
| 11 | "technical debt is a critical blocker" | 🚨 Critical Issue |
| 12 | "recommendation is to ship limited version" | ⚠️ Key Decision Point |

### Demo Talking Points
- **"Watch the Alerts section"** — show the panel lighting up each time a key moment is detected
- **"Notice the Summary evolving"** — it's not a transcript, it's an understanding
- **"These questions were never asked"** — the AI generated them proactively
- **"Recommended Actions appeared before the meeting ended"** — the system is ahead of the participants

---

## 4. Technical Decisions (2 min)

### AlertAgent — Pattern Matching, Not LLM
The AlertAgent uses keyword pattern matching rather than an LLM call. This is intentional:
- **Zero latency** — fires instantly, no network hop
- **100% reliable** — no hallucination risk on detection
- **Always-on** — works in mock mode or live mode identically  
- The LLM is reserved for *generative* tasks (summary, questions, insights, directions)

### DirectionAgent — Context-Aware Templates
In mock mode, DirectionAgent maps detected keywords to pre-written, domain-specific action templates. This means the directions are always coherent and actionable, even without an API key.

### RAG with Recency Boost
Standard vector similarity retrieval can favour older, semantically dominant chunks. The recency boost ensures the *most recent* chunk is always included in the context window, giving agents awareness of what just happened — not just what was most discussed.

### Node.js + Python Split
Node.js handles WebSocket fan-out and stream timing (I/O bound).  
Python handles all AI computation (CPU/model bound).  
Neither blocks the other.

---

## 5. Learnings (2 min)

### The "Wow" Moment Is Architecture, Not Output
The impressive part isn't the text in the panels — it's that **the system reacts without being asked**. The AlertAgent firing on "Legal has flagged concerns" feels qualitatively different from getting the same info via search.

### Before vs. After: What Changed in v2

| Aspect | v1 | v2 |
|--------|----|----|
| Demo content | Generic AI text | Critical product meeting |
| Agent count | 3 (passive) | 5 (2 active agents) |
| Alert system | None | Pattern-based, instant |
| Next steps | None | DirectionAgent output |
| Panels | 3-column grid | Full-width Alerts + 2×2 grid |
| RAG | Similarity-only | Similarity + recency boost |
| Demo narrative | Implicit | Explicit script + table |

### Challenges
- **Testing streaming systems** requires careful async coordination — the integration tests simulate the full pipeline with mocked HTTP
- **ChromaDB compatibility** across versions required custom hash-based embeddings to avoid model downloads
- **Alert precision** — "concern" was initially a conflict keyword but matched too broadly; it was removed in favour of more specific terms

### Limitations
- In mock mode, LLM outputs are template-based — real OpenAI integration produces richer, more varied text
- AlertAgent does not detect negations ("no risk" still matches "risk")
- The demo stream is pre-scripted — a real audio or live transcript feed would require a transcription layer (Whisper)

### What I'd Do Differently
- Add a **severity score** to alerts (low / medium / high) based on multiple pattern matches
- Stream the AI response tokens back rather than waiting for the full response
- Build a **timeline view** so the audience can see the entire meeting arc at a glance

---

## 6. Running Tests

```bash
# Backend (Jest) — 14 tests
cd backend && npm test

# AI Layer (pytest) — 72 tests
cd ai && MOCK_MODE=true pytest tests/ -v
```

All tests pass in mock mode without any API keys.

---

## Quick Start (All Services)

```bash
npm install          # installs concurrently at root
npm run dev          # starts AI server + Backend + Frontend concurrently
```

Open **http://localhost:3000** — streaming starts automatically after 1 second.
