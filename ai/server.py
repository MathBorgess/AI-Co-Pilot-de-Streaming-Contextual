"""FastAPI server for the AI Co-Pilot."""
from orchestrator import Orchestrator
import os
import sys
import base64
import io
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))


app = FastAPI(title="AI Co-Pilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = Orchestrator()


class ChunkRequest(BaseModel):
    chunk: str
    chunkIndex: Optional[int] = 0
    totalChunks: Optional[int] = 0


class TranscribeRequest(BaseModel):
    audioBase64: str
    mimeType: Optional[str] = "audio/webm"


@app.get("/health")
def health():
    return {"status": "ok", "mode": "mock" if os.getenv("MOCK_MODE", "true").lower() == "true" else "live"}


@app.post("/process")
def process_chunk(request: ChunkRequest):
    """Process a text chunk through the RAG + Agents pipeline."""
    if not request.chunk or not request.chunk.strip():
        raise HTTPException(status_code=400, detail="chunk cannot be empty")

    print(f"[AUDIO] Received chunk #{request.chunkIndex} (len={len(request.chunk)})")
    print(f"[TRANSCRIPTION] {request.chunk[:200]}")

    result = orchestrator.process(
        chunk=request.chunk,
        chunk_index=request.chunkIndex,
        total_chunks=request.totalChunks,
    )

    print(f"[RAG] Stored chunk id={result.get('chunkId')} - context_items={orchestrator.rag.chunk_count()}")
    print(f"[ALERT_AGENT] alerts={len(result.get('alerts', []))} [ACTION_AGENT] actions={len(result.get('actions', []))}")

    return result


@app.post("/reset")
def reset():
    """Reset all agent and RAG state."""
    orchestrator.reset()
    return {"status": "reset"}


def _transcribe_audio(audio_bytes: bytes, mime_type: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if os.getenv("MOCK_MODE", "true").lower() == "true":
        return ""
    if os.getenv("DISABLE_TRANSCRIPTION", "false").lower() == "true":
        return ""
    if not api_key or api_key == "your_key_here":
        return ""

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.webm" if "webm" in (
            mime_type or "") else "audio.wav"
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text",
        )
        if isinstance(result, str):
            return result.strip()
        return getattr(result, "text", "").strip()
    except Exception as e:
        print(f"[Transcribe] Error: {e}")
        return ""


@app.post("/transcribe")
def transcribe_audio(request: TranscribeRequest):
    if not request.audioBase64:
        raise HTTPException(
            status_code=400, detail="audioBase64 cannot be empty")

    try:
        audio_bytes = base64.b64decode(request.audioBase64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"invalid base64: {e}")

    text = _transcribe_audio(audio_bytes, request.mimeType or "audio/webm")
    print(f"[TRANSCRIPTION] transcribe result length={len(text)}")

    return {
        "text": text,
        "isFinal": True,
        "mode": "whisper" if text else "mock",
    }


@app.get("/stats")
def stats():
    """Get current stats."""
    return {
        "chunks_processed": orchestrator.chunk_count,
        "chunks_in_rag": orchestrator.rag.chunk_count(),
        "current_summary": orchestrator.summarizer.current_summary,
        "questions_count": len(orchestrator.question_generator.all_questions),
        "insights_count": len(orchestrator.insight_generator.all_insights),
        "actions_count": len(orchestrator.action_agent.current_actions),
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"[AI Server] Starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
